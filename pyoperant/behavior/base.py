import logging
import traceback
import logging.handlers
import os
import sys
import socket
import datetime as dt
from pyoperant import utils, components, local, hwio, configure
from pyoperant import ComponentError, InterfaceError, EndExperiment
from pyoperant import states, trials, subjects, blocks

logger = logging.getLogger(__name__)


def _log_except_hook(*exc_info):
    text = "".join(traceback.format_exception(*exc_info))
    logging.error("Unhandled exception: %s", text)


class BaseExp(object):
    """ Base class for an experiment. This controls most of the experiment logic
    so you only have to implement specifics for your behavior.

    Parameters
    ----------
    name: string
        Name of this experiment
    desc: string
        Long description of this experiment
    debug: bool
        Flag for debugging, switches the logging stream handler between debug
        and info levels
    light_schedule:
        The light schedule for the experiment. either 'sun' or
        a tuple of (starttime,endtime) tuples in (hhmm,hhmm) form defining
        time intervals for the lights to be on
    experiment_path: string
        Path to the experiment directory
    stim_path: string (<experiment_path>/stims)
        Path to stimulus directory
    subject: an instance of a Subject() object
        The subject of the current experiment
    panel: instance of local Panel() object
        The full hardware panel. It must implement all required attributes for
        the current experiment.
    log_handlers: list of dictionaries
        Currently supported handler types are file and email (in addition to
        the default stream handler)
    blocks: list of Block() objects
        Initialized block objects that contain the conditions to be tested.

    Methods:
    run() -- runs the experiment

    """

    # This should contain all states to be used in the state machine.
    # "idle" is the only one that is required.
    STATE_DICT = dict(idle=states.Idle,
                      sleep=states.Sleep,
                      session=states.Session)

    # All panels should have these methods, but it's best to include them in every experiment just in case
    req_panel_attr = ["sleep",
                      "reset",
                      "idle",
                      "ready"]

    # All experiments should store at least these fields but probably more
    fields_to_save = ['session',
                      'index',
                      'time']

    def __init__(self,
                 states,
                 panel,
                 block_queue,
                 subject,
                 name='',
                 description='',
                 datastore="csv",
                 debug=False,
                 filetime_fmt='%Y%m%d%H%M%S',
                 experiment_path='',
                 log_handlers=None,
                 *args, **kwargs):

        super(BaseExp, self).__init__()

        # Initialize experiment parameters received as input
        self.name = name
        self.description = description
        self.debug = debug
        self.timestamp = dt.datetime.now().strftime(filetime_fmt)

        if not os.path.exists(experiment_path):
            logger.debug("Creating %s" % experiment_path)
            os.makedirs(experiment_path)

        # configure logging
        if not log_handlers:
            log_handlers = dict()
        self.log_handlers = log_handlers
        # Should a file log be mandatory and set up by default? If so, bring it
        # out of the for loop
        self.log_config()
        for handler_config in self.log_handlers.keys():
            if handler_config == "file":
                self.add_file_handler()
            elif handler_config == "email":
                self.add_email_handler()

        self.panel = panel
        logger.info('panel %s initialized' % self.panel.__class__.__name__)

        logger.info("Preparing block objects")
        self.block_queue = block_queue

        logger.info("Preparing subject object")
        self.subject = subject
        output_file = "%s_trialdata_%s.%s" % (subject.name, self.timestamp,
                                              datastore)
        self.subject.filename = os.path.join(experiment_path, output_file)
        self.subject.create_datastore(self.fields_to_save)

        self.session_id = 0

        # Add variables into parameters to save out a config file. I'd rather do this outside of the experiment, perhaps when loading the config file.
        self.parameters = kwargs
        self.parameters['filetime_fmt'] = filetime_fmt
        self.parameters['light_schedule'] = light_schedule
        self.parameters['idle_poll_interval'] = idle_poll_interval
        self.parameters['experiment_path'] = experiment_path
        self.parameters['stim_path'] = stim_path
        self.parameters['subject'] = subject.name
        self.parameters['log_handlers'] = log_handlers

        #
        # if 'shape' not in self.parameters or self.parameters['shape'] not in ['block1', 'block2', 'block3', 'block4', 'block5']:
        #     self.parameters['shape'] = None
        #
        # self.shaper = shape.Shaper(self.panel, logger, self.parameters, self.log_error_callback)

    def save(self):
        self.snapshot_f = os.path.join(self.parameters['experiment_path'], self.timestamp+'.json')
        logger.debug("Saving snapshot of parameters to %s" % self.snapshot_f)
        if self.snapshot_f.lower().endswith(".json"):
            configure.ConfigureJSON.save(self.parameters, self.snapshot_f, overwrite=True)
        elif self.snapshot_f.lower().endswith(".yaml"):
            configure.ConfigureYAML.save(self.parameters, self.snapshot_f, overwrite=True)

    # Logging configure methods
    def log_config(self):

        if "stream" in self.log_handlers:
            self.log_level = self.log_handlers["stream"].get("level", logging.INFO)
        elif self.debug:
            self.log_level = logging.DEBUG
        else:
            self.log_level = logging.INFO

        sys.excepthook = _log_except_hook # send uncaught exceptions to log file

        logging.basicConfig(level=self.log_level,
                            format='"%(asctime)s","%(levelname)s","%(message)s"')

        # Make sure that the stream handler has the requested log level.
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(self.log_level)

    def add_file_handler(self):
        """ Add a file handler to the root logger using either default
        settings or settings from the config file
        """
        self.log_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.log')
        props = dict()
        if "file" in self.log_handlers:
            props = self.log_handlers["file"]
            if props["filename"]:
                self.log_file = os.path.join(self.parameters["experiment_path"], props["filename"])

        file_handler = logging.FileHandler(self.log_file)
        level = props.get("level", self.log_level)
        formatter = props.get("format", '"%(asctime)s","%(levelname)s","%(message)s"')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(formatter))
        root_logger = logging.getLogger()
        # Make sure the root logger's level is not too high
        if root_logger.level > level:
            root_logger.setLevel(level)
        root_logger.addHandler(file_handler)
        logger.debug("File handler added to %s with level %d" % (self.log_file, level))

    def add_email_handler(self):
        """Add an email handler to the root logger using configurations from the
        config file.
        """
        handler_config = self.log_handlers["email"]
        level = handler_config.pop("level", logging.ERROR)
        email_handler = logging.handlers.SMTPHandler(**handler_config)
        email_handler.setLevel(level)

        heading = '%s\n' % (self.parameters['subject'])
        formatter = logging.Formatter(heading+'%(levelname)s at %(asctime)s:\n%(message)s')
        email_handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        # Make sure the root logger's level is not too high
        if root_logger.level > level:
            root_logger.setLevel(level)
        root_logger.addHandler(email_handler)
        logger.debug("Email handler added to %s with level %d" % (",".join(email_handler.toaddrs), level))

    # Scheduling methods
    def check_light_schedule(self):
        """returns true if the lights should be on"""

        lights_on = utils.check_time(self.parameters['light_schedule'])
        logger.debug("Checking light schedule: %s" % lights_on)
        return lights_on

    def check_session_schedule(self):
        """returns True if the subject should be running sessions"""

        session_on = False
        if "session_schedule" in self.parameters:
            session_on = utils.check_time(self.parameters["session_schedule"])

        logger.debug("Checking session schedule: %s" % session_on)
        return session_on

    def schedule_current_session(self):

        duration = self.parameters.get("session_duration", -dt.timedelta(minutes=1))
        start = getattr(self, "session_start_time", dt.datetime.now())
        schedule = (start.strftime("%H:%M"), (start + duration).strftime("%H:%M"))
        self.parameters.setdefault("session_schedule", []).append(schedule)
        logger.info("Scheduled current session for %s" % " to ".join(schedule))

    def schedule_next_session(self):

        current_time = dt.datetime.now()
        delay = self.parameters.get("intersession_interval", -dt.timedelta(minutes=1))
        start = current_time + delay
        stop = current_time - dt.timedelta(minutes=1)
        schedule = (start.strftime("%H:%M"), (start + duration).strftime("%H:%M"))
        self.parameters.setdefault("session_schedule", []).append(schedule)
        logger.info("Scheduled next session for %s" % " to ".join(schedule))

    def end(self):

        self.panel.sleep()
        raise EndExperiment

    def shape(self):
        """
        This will house a method to run shaping.
        """

        pass

    # State and trial logic. It might be good to have these methods do some common sense functions / logging
    def run(self):

        for attr in self.req_panel_attr:
            logger.debug("Checking that panel has attribute %s" % attr)
            assert hasattr(self.panel, attr)

        logger.debug("Resetting panel")
        self.panel.reset()
        self.save()
        # self.init_summary()

        logger.info('%s: running %s with parameters in %s' % (self.name,
                                                              self.__class__.__name__,
                                                              self.snapshot_f,
                                                              )
                      )
        if self.parameters['shape']:
            logger.info("Running shaping")
            self.shaper.run_shape(self.parameters['shape'])

        for state in self.states:
            if state.check():
                with state as self.state:
                    self.state.run()

    ## Session Flow
    def session_pre(self):
        """ Runs before the session starts. Initializes the block queue and
        records the session start time.
        """
        logger.debug("Beginning session")
        self.session_id += 1
        self.session_start_time = dt.datetime.now()
        self.panel.ready()

    def session_main(self):
        """ Runs the session by looping over the block queue and then running
        each trial in each block.
        """

        for self.this_block in self.block_queue:
            self.this_block.experiment = self
            logger.info("Beginning block #%d" % self.this_block.index)
            for trial in self.this_block:
                trial.run()

    def session_post(self):
        """ Closes out the sessions
        """

        self.panel.idle()
        self.session_end_time = dt.datetime.now()
        logger.info("Finishing session %d at %s" % (self.session_id, self.session_end_time.ctime()))
        if self.session_id < self.parameters.get("num_sessions", 1):
            self.schedule_next_session()
        else:
            logger.info("Finished all sessions.")
            self.end()

    # Defining the different trial states. If any of these are not needed by the behavior, just don't define them in your subclass
    def trial_pre(self):
        pass

    def stimulus_pre(self):
        pass

    def stimulus_main(self):
        pass

    def stimulus_post(self):
        pass

    def response_pre(self):
        pass

    def response_main(self):
        pass

    def response_post(self):
        pass

    def reward_pre(self):
        pass

    def reward_main(self):
        pass

    def reward_post(self):
        pass

    def punish_pre(self):
        pass

    def punish_main(self):
        pass

    def punish_post(self):
        pass

    def trial_post(self):
        pass

    # gentner-lab specific functions
    def init_summary(self):
        """ initializes an empty summary dictionary """
        self.summary = {'trials': 0,
                        'feeds': 0,
                        'hopper_failures': 0,
                        'hopper_wont_go_down': 0,
                        'hopper_already_up': 0,
                        'responses_during_feed': 0,
                        'responses': 0,
                        'last_trial_time': [],
                        }

    def write_summary(self):
        """ takes in a summary dictionary and options and writes to the bird's summaryDAT"""
        summary_file = os.path.join(self.parameters['experiment_path'],self.parameters['subject'][1:]+'.summaryDAT')
        with open(summary_file,'wb') as f:
            f.write("Trials this session: %s\n" % self.summary['trials'])
            f.write("Last trial run @: %s\n" % self.summary['last_trial_time'])
            f.write("Feeder ops today: %i\n" % self.summary['feeds'])
            f.write("Hopper failures today: %i\n" % self.summary['hopper_failures'])
            f.write("Hopper won't go down failures today: %i\n" % self.summary['hopper_wont_go_down'])
            f.write("Hopper already up failures today: %i\n" % self.summary['hopper_already_up'])
            f.write("Responses during feed: %i\n" % self.summary['responses_during_feed'])
            f.write("Rf'd responses: %i\n" % self.summary['responses'])

    def log_error_callback(self, err):
        if err.__class__ is InterfaceError or err.__class__ is ComponentError:
            logger.critical(str(err))
