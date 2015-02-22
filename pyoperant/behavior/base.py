import logging, traceback
import os, sys, socket
import datetime as dt
from pyoperant import utils, components, local, hwio, configure
from pyoperant import ComponentError, InterfaceError
from pyoperant.behavior import shape
try:
    import simplejson as json
except ImportError:
    import json

def _log_except_hook(*exc_info):
    text = "".join(traceback.format_exception(*exc_info))
    logging.error("Unhandled exception: %s", text)

class BaseExp(object):
    """Base class for an experiment.

    Keyword arguments:
    name -- name of this experiment
    desc -- long description of this experiment
    debug -- (bool) flag for debugging (default=False)
    light_schedule  -- the light schedule for the experiment. either 'sun' or
        a tuple of (starttime,endtime) tuples in (hhmm,hhmm) form defining
        time intervals for the lights to be on
    experiment_path -- path to the experiment
    stim_path -- path to stimuli (default = <experiment_path>/stims)
    subject -- identifier of the subject
    panel -- instance of local Panel() object

    Methods:
    run() -- runs the experiment

    """

    # This should contain all states to be used in the state machine.
    # "idle" is the only one that is required.
    STATE_DICT = dict(idle=states.Idle,
                      sleep=states.Sleep,
                      session=states.Session)

    req_panel_attr = ["sleep", "reset"]

    def __init__(self,
                 name='',
                 description='',
                 debug=False,
                 filetime_fmt='%Y%m%d%H%M%S',
                 light_schedule='sun',
                 idle_poll_interval = 60.0,
                 experiment_path='',
                 stim_path='',
                 subject='',
                 panel=None,
                 log_handlers=None,
                 *args, **kwargs):

        super(BaseExp,  self).__init__()

        # Initialize experiment parameters received as input
        self.name = name
        self.description = description
        self.debug = debug
        self.timestamp = dt.datetime.now().strftime(filetime_fmt)
        self.parameters = kwargs
        self.parameters['filetime_fmt'] = filetime_fmt
        self.parameters['light_schedule'] = light_schedule
        self.parameters['idle_poll_interval'] = idle_poll_interval
        self.parameters['experiment_path'] = experiment_path
        if stim_path == '':
            self.parameters['stim_path'] = os.path.join(experiment_path,'stims')
        else:
            self.parameters['stim_path'] = stim_path
        self.parameters['subject'] = subject

        # configure logging
        if not log_handlers:
            log_handlers = dict()
        self.parameters['log_handlers'] = log_handlers
        self.log_config()
        self.add_file_handler()
        for handler_config in log_handlers.keys():
            if handler.config == "email":
                self.add_email_handler()

        self.panel = panel
        self.log.info('panel %s initialized' % self.parameters['panel_name'])
        #
        # if 'shape' not in self.parameters or self.parameters['shape'] not in ['block1', 'block2', 'block3', 'block4', 'block5']:
        #     self.parameters['shape'] = None
        #
        # self.shaper = shape.Shaper(self.panel, self.log, self.parameters, self.log_error_callback)

    def save(self):
        self.snapshot_f = os.path.join(self.parameters['experiment_path'], self.timestamp+'.json')
        self.log.debug("Saving snapshot of parameters to %s" % self.snapshot_f)
        if self.snapshot_f.lower().endswith(".json"):
            configure.ConfigureJSON.save(self.parameters, self.snapshot_f)
        elif self.snapshot_f.lower().endswith(".yaml"):
            configure.ConfigureYAML.save(self.parameters, self.snapshot_f)

    # Logging configure methods
    def log_config(self):

        if self.debug:
            self.log_level = logging.DEBUG
        else:
            self.log_level = logging.INFO
        sys.excepthook = _log_except_hook # send uncaught exceptions to log file

        logging.basicConfig(level=self.log_level,
                            format='"%(asctime)s","%(levelname)s","%(message)s"')
        self.log = logging.getLogger(self.__class__.__name__)

    def add_file_handler(self):

        self.log_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.log')
        props = dict()
        if "file" in self.parameters["log_handlers"]:
            props = self.parameters["log_handlers"]["file"]
            if props["filename"]:
                self.log_file = os.path.join(self.parameters["experiment_path"], props["filename"])

        file_handler = logging.handlers.FileHandler()
        level = props.get("level", self.log_level)
        file_handler.setLevel(level)
        self.log.addHandler(file_handler)
        self.log.debug("File handler added to %s with level %d" % (self.log_file, level))

    def add_email_handler(self):

        handler_config = self.properties["log_handlers"]["email"]
        level = handler_config.pop("level", logging.ERROR)
        email_handler = logging.handlers.SMTPHandler(**handler_config)
        email_handler.setLevel(level)

        heading = '%s\n' % (self.parameters['subject'])
        formatter = logging.Formatter(heading+'%(levelname)s at %(asctime)s:\n%(message)s')
        email_handler.setFormatter(formatter)
        self.log.addHandler(email_handler)
        self.log.debug("Email handler added to %s with level %d" % (",".join(email_handler.toaddrs), level))

    # Scheduling methods
    def check_light_schedule(self):
        """returns true if the lights should be on"""

        lights_on = utils.check_time(self.parameters['light_schedule'])
        self.log.debug("Checking light schedule: %s" % lights_on)
        return lights_on

    def check_session_schedule(self):
        """returns True if the subject should be running sessions"""

        session_on = False
        if "session_schedule" in self.parameters:
            session_on = utils.check_time(self.parameters["session_schedule"])

        self.log.debug("Checking session schedule: %s" % session_on)
        return session_on

    def schedule_current_session(self):

        duration = self.parameters.get("session_duration", -dt.timedelta(minutes=1))
        start = getattr(self, "session_start_time", dt.datetime.now())
        schedule = (start.strftime("%H:%M"), (start + duration).strftime("%H:%M"))
        self.parameters.setdefault("session_schedule", []).append(schedule)
        self.log.debug("Scheduled current session for %s" % " to ".join(schedule))

    def schedule_next_session(self):

        current_time = dt.datetime.now()
        delay = self.parameters.get("intersession_interval", -dt.timedelta(minutes=1))
        start = current_time + delay
        stop = current_time - dt.timedelta(minutes=1)
        schedule = (start.strftime("%H:%M"), (start + duration).strftime("%H:%M"))
        self.parameters.setdefault("session_schedule", []).append(schedule)
        self.log.debug("Scheduled next session for %s" % " to ".join(schedule))

    # State and trial logic. It might be good to have these methods do some common sense functions / logging
    def run(self):

        for attr in self.req_panel_attr:
            self.log.debug("Checking that panel has attribute %s" % attr)
            assert hasattr(self.panel, attr)

        self.log.debug("Resetting panel")
        self.panel.reset()
        self.save()
        # self.init_summary()

        self.log.info('%s: running %s with parameters in %s' % (self.name,
                                                                self.__class__.__name__,
                                                                self.snapshot_f,
                                                                )
                      )
        if self.parameters['shape']:
            self.log.info("Running shaping")
            self.shaper.run_shape(self.parameters['shape'])

        while True:
            self.log.debug("Entering state machine")
            states.run_state_machine(start_in='idle',
                                     error_state='idle',
                                     **self.STATE_DICT)

    # session
    def session_pre(self):
        pass

    def session_main(self):
        pass

    def session_post(self):
        pass

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

    def consequate_pre(self):
        pass

    def consequate_main(self):
        pass

    def consequate_post(self):
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
            self.log.critical(str(err))
