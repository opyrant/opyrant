#!/usr/local/bin/python

import os
import sys
import logging
import csv
import copy
import datetime as dt
import random
# import ipdb
from pyoperant.behavior import base, shape
from pyoperant.errors import EndSession
from pyoperant import components, utils, reinf, queues


class GoNoGoInterrupt(base.BaseExp):
    """A go no-go interruption experiment

    Parameters
    ----------
    stim_path
    subject
    experiment_path
    session_schedule
    go_probability
    session_duration
    intersession_interval
    num_sessions

    Attributes
    ----------
    req_panel_attr : list
        list of the panel attributes that are required for this behavior
    fields_to_save : list
        list of the fields of the Trial object that will be saved
    trials : list
        all of the trials that have run
    shaper : Shaper
        the protocol for shaping
    parameters : dict
        all additional parameters for the experiment
    data_csv : string
        path to csv file to save data
    reinf_sched : object
        does logic on reinforcement



    """
    def __init__(self, *args, **kwargs):

        super(GoNoGoInterrupt,  self).__init__(*args, **kwargs)

        # Which components must be present in the panel
        # Should move this to: "stimulus", "response_port", "reward"
        # Make it describe the behavior and then have the physical implementation described by the panel object
        self.req_panel_attr.extend(['speaker', 'response_port', 'reward', 'ready', 'idle'])

        ### Subject object here

        # Columns for the CSV file where data is written
        # This should go in a subject object
        self.fields_to_save = ['session',
                               'index',
                               'time',
                               'stimulus',
                               'class_',
                               'response',
                               'correct',  # redundant
                               'rt',
                               'reward',  # redundant
                               'max_wait',
                               ]

        # Create a subject object
        self.subject = Subject(name=self.subject_name, datastore="csv", output_path="/path/to/datastore")

        # This sets up the reinforcement schedule. Defaults to continuous where every correct trial is rewarded
        self.reinforcement = reinf.ContinuousReinforcement()

        # Begin rewrite
        # Generate stimulus class objects rewarded_stimuli and nonrewarded_stimuli
        rewarded_stimuli = StimClass(name="Reward", path=stim_path)
        nonrewarded_stimuli = StimClass(name="Unrewarded", path=other_stim_path)
        # self.trial_queue = queues.RandomQueue([(rewarded_stimuli, reward_probability), (nonrewarded_stimuli, 1 - reward_probability)])
        # Maybe this should be a BlockHandler?
        self.blocks = BlockHandler(queue=queues.random_queue)
        self.blocks = queues.RandomQueue()

        # Add weights to random queue to adjust the probability of a go stim GROSSS
        default_block = dict(queue="random",
                             conditions=[{"class": "Go"},
                                         {"class": "NoGo"}],
                             tr_max=400,
                             weights=[int(400 * self.parameters["go_probability"]), int(400 * (1 - self.parameters["go_probability"]))])
        blocks = dict(default=default_block)
        self.parameters["block_design"] = dict(blocks=blocks,
                                               order=["default"])

        self.parameters["stims"] = dict()
        stim_path = os.path.join(self.parameters["stim_path"], "go")
        self.parameters["stims"]["Go"] = map(lambda fname: os.path.join(stim_path, fname), os.listdir(stim_path))
        stim_path = os.path.join(self.parameters["stim_path"], "nogo")
        self.parameters["stims"]["NoGo"] = map(lambda fname: os.path.join(stim_path, fname), os.listdir(stim_path))

        # Initialize some parameters
        self.trials = []
        self.session_id = 0

    def shape(self):
        """
        This will house a method to run shaping.
        """

        pass


    # Stupid scheduling shit. Need to rethink this

    # Use self.this_block.check_complete() instead
    # def check_session_schedule(self):
    #     """ Check the session schedule
    #
    #     Returns
    #     -------
    #     bool
    #         True if sessions should be running
    #     """
    #     if len(self.parameters["session_schedule"]):
    #         return utils.check_time(self.parameters['session_schedule'])
    #     else:
    #         return False

    def schedule_current_session(self):

        current_time = dt.datetime.now()
        stop_time = current_time + dt.timedelta(minutes=self.parameters["session_duration"])
        self.parameters["session_schedule"] = [(current_time.strftime("%H:%M"), stop_time.strftime("%H:%M"))]
        self.session_end_time = stop_time

    def schedule_next_session(self):

        current_time = dt.datetime.now()
        start_time = current_time + dt.timedelta(minutes=self.parameters["intersession_interval"])
        stop_time = current_time - dt.timedelta(minutes=1)
        self.parameters["session_schedule"] = [(start_time.strftime("%H:%M"), stop_time.strftime("%H:%M"))]

    ## Session Flow
    def session_pre(self):
        """ Runs before the session starts
        """
        self.log.debug("Beginning session")

        return 'main'

    def session_main(self):
        """ Runs the sessions

        Inside of `session_main`, we loop through sessions and through the trials within
        them. This relies heavily on the 'block_design' parameter, which controls trial
        conditions and the selection of queues to generate trial conditions.

        """

        # What we want!
        self.
        for self.this_block in self.blocks:
            for trial in block.trials:
                trial.run()
        #
        # def run_trial_queue():
        #     for tr_cond in self.trial_queue:
        #         self.new_trial(tr_cond)
        #         self.run_trial()
        #         self.log.debug("Moving to next trial")


                # grab the block details
                # A dictionary with the block queue type (e.g. random) and a list of classes (e.g. L) This nomenclature is rough. Classes are conditions, it seems
                # blk = copy.deepcopy(self.parameters['block_design']['blocks'][sn_cond])

                # Load up stimuli - Probably need this to happen because we need fast stimulus triggering
                # self.load_trials()

                # Turn on the center light
                self.log.debug("Turning response port light on to start the session")
                # Maybe move to self.panel.ready() and self.panel.idle()
                self.panel.ready()

                # Poll for a response - This should now happen in the trial_pre section
                self.log.debug("Begin polling for the initial peck")
                # self.first_trial_start = self.panel.response_port.poll()

                # Once a peck is registered, begin the trial and set the session schedule
                self.log.info("First peck registered at %s" % self.first_trial_start.ctime())
                self.schedule_current_session()
                self.log.debug("Current session scheduled to end at %s" % self.parameters["session_schedule"][0][1])
                try:
                    # Start running trials
                    run_trial_queue()
                except EndSession:
                    return 'post'

            self.session_queue = None

        else:
            try:
                run_trial_queue()
            except EndSession:
                return 'post'

        return 'post'

    ## Trial Flow
    # def new_trial(self, conditions=None):
    #     """Creates a new trial and appends it to the trial list
    #
    #     If `self.do_correction` is `True`, then the conditions are ignored and a new
    #     trial is created which copies the conditions of the last trial.
    #
    #     Parameters
    #     ----------
    #     conditions : dict
    #         The conditions dict must have a 'class' key, which specifies the trial
    #         class. The entire dict is passed to `exp.get_stimuli()` as keyword
    #         arguments and saved to the trial annotations.
    #
    #     """
    #
    #     index = len(self.trials)
    #     trial = utils.Trial(index=index)
    #     trial.class_ = conditions['class']
    #     trial_stim = self.get_stimuli(**conditions)
    #     trial.stimulus_event = trial_stim
    #     trial.stimulus = trial.stimulus_event.name
    #
    #     trial.session = self.session_id
    #     trial.annotate(**conditions)
    #
    #     self.trials.append(trial)
    #     self.this_trial = trial
    #
    #
    #
    #     return True

    # Now encapsulated in stimulus condition object
    # def get_stimuli(self,**conditions):
    #     """ Get the trial's stimuli from the conditions
    #
    #     Returns
    #     -------
    #     stim, epochs : Event, list
    #
    #
    #     """
    #     stim_file = random.choice(self.parameters['stims'][conditions["class"]])
    #     stim = utils.auditory_stim_from_wav(stim_file)
    #     return stim

    # def run_trial(self):
    #
    #     utils.run_state_machine(start_in="trial_pre",
    #                             error_state="trial_post", # probably should do some error handling
    #                             error_callback=self.log_error_callback,
    #                             stimulus_pre=self.stimulus_pre,
    #                             stimulus_main=self.stimulus_main,
    #                             response=self.response_main,
    #                             reward=self.reward_main,
    #                             trial_pre=self.trial_pre,
    #                             trial_post=self.trial_post)

    def trial_pre(self):
        ''' this is where we initialize a trial'''
        if not self.start_immediately:
            self.response_port.poll()

    def stimulus_pre(self):
        # wait for bird to peck
        self.log.debug("stimulus_pre - queuing file in speaker")
        self.panel.speaker.queue(self.this_trial.stimulus_event.file_origin)
        self.log.debug("wavfile queued")

    def stimulus_main(self):
        ##play stimulus
        self.log.debug("stimulus_main")
        self.this_trial.time = dt.datetime.now()
        self.log.info("Trial %d - %s - %s - %s" % (self.this_trial.index,
                                                   self.this_trial.time.strftime("%H:%M:%S"),
                                                   self.this_trial.class_,
                                                   self.this_trial.stimulus))
        # ipdb.set_trace()
        self.panel.speaker.play() # already queued in stimulus_pre()
        self.log.debug("played stimulus")

    def stimulus_post(self):

        pass

    def response_pre(self):

        pass

    def response_main(self):

        self.log.debug("response_main")

        utils.wait(self.this_trial.annotations["min_wait"])
        self.log.debug("waited %3.2f seconds" % self.this_trial.annotations["min_wait"])

        self.this_trial.response_time = self.panel.response_port.poll(self.this_trial.annotations['max_wait'])
        self.log.debug("Received peck or timeout. Stopping playback")

        self.panel.speaker.stop()
        self.log.debug("Playback stopped")

        if self.this_trial.peck_time is None:
            self.this_trial.response = 0
        else:
            self.this_trial.response = 1
            self.this_trial.rt = self.this_trial.response_time - self.this_trial.time


        # if self.this_trial.peck_time is None:
        #     self.log.debug("No peck detected")
        #     self.this_trial.response = 0
        #     # self.this_trial.response = 0
        #     # if self.this_trial.class_ == "NoGo":
        #     #     self.log.debug("No Go stimulus. Giving reward")
        #     #     self.this_trial.correct = 1
        #     #     self.this_trial.reward = 1
        #     #     return "reward"
        #     # else:
        #     #     self.log.debug("Go stimulus. No reward")
        #     #     self.this_trial.correct = 0
        #     #     self.this_trial.reward = 0
        #     #     return "trial_post"
        #
        # else:
        #     self.this_trial.response = 1
        #
        #     if self.this_trial.class_ == "Go":
        #         self.this_trial.correct = 1
        #     else:
        #         self.this_trial.correct = 0
        #     self.this_trial.rt = self.this_trial.peck_time - self.this_trial.time
        #     self.this_trial.reward = 0
        #
        #     self.log.info("Peck detected. RT = %3.2f" % self.this_trial.rt.total_seconds())
        #     return "trial_post"

    def response_post(self):

        pass

    def consequate_pre(self):

        pass

    def consequate_main(self):

        if self.this_trial.response == self.this_trial.stimulus_condition.response:
            self.this_trial.correct = True
        else:
            self.this_trial.correct = False

        # This is maybe a bit overly done
        if self.reinforcement.consequate(self.this_trial): # Should we reinforce?
            if self.this_trial.correct:
                self.reward()
            else:
                self.punish()
        else:
            pass

    def consequate_post(self):

        pass

    def reward(self):

        self.log.debug("reward_main")
        self.summary['feeds'] += 1
        value = self.parameters['reward_duration']
        self.log.info("Supplying reward for %3.2f seconds" % value)
        reward_event = self.panel.reward(value=value)

    def punish(self):

        self.log.debug("punish")

    def trial_post(self):
        '''things to do at the end of a trial'''

        self.log.debug("trial_post")
        self.summary['trials'] += 1
        self.summary['last_trial_time'] = self.this_trial.time.ctime()

        # self.log.debug("Saving trial data")
        # self.save_trial(self.this_trial)

        if self.check_session_schedule()==False:
            self.log.debug("Session has run long enough. Ending")
            raise EndSession

        # if self.this_trial.peck_time is None:
        #     self.log.debug("Waiting for peck to start a new trial")
        #     timeout = (self.session_end_time - dt.datetime.now()).total_seconds()
        #     pecked = self.panel.response_port.poll(timeout)
        #     if pecked is None:
        #         raise EndSession


    # def save_trial(self,trial):
    #     '''write trial results to CSV'''
    #
    #     trial_dict = {}
    #     for field in self.fields_to_save:
    #         try:
    #             trial_dict[field] = getattr(trial,field)
    #         except AttributeError:
    #             trial_dict[field] = trial.annotations[field]
    #
    #     with open(self.data_csv,'ab') as data_fh:
    #         trialWriter = csv.DictWriter(data_fh,fieldnames=self.fields_to_save,extrasaction='ignore')
    #         trialWriter.writerow(trial_dict)

    def session_post(self):
        """ Closes out the sessions
        """
        # If session id is less than number of sessions for the day, set the session schedule for the next start
        self.session_end_time = dt.datetime.now()
        # self.session_queue = None
        # self.trial_queue = None
        self.log.info("Finishing session %d at %s" % (self.session_id, self.session_end_time.ctime()))
        if self.session_id < self.parameters["num_sessions"]:
            self.schedule_next_session()
            self.log.info("Next session scheduled to start at %s" % self.parameters["session_schedule"][0][0])
        else:
            self.log.info("Finished all sessions.")



if __name__ == "__main__":

    try: import simplejson as json
    except ImportError: import json
    from pyoperant.tlab.local_tlab import PANELS
    from pyoperant.tlab.go_no_go_interrupt import GoNoGoInterrupt

    #cmd_line = utils.parse_commandline()
    config_file = "/Users/tylerlee/code/pyoperant/pyoperant/tlab/go_no_go_interrupt_config.json"
    with open(config_file, 'rb') as config:
            parameters = json.load(config)

    #assert utils.check_cmdline_params(parameters, cmd_line)

    if parameters['debug']:
        print parameters
        print PANELS

    panel = PANELS[parameters['panel_name']]()
    if isinstance(parameters["session_schedule"], list):
        if isinstance(parameters["session_schedule"][0], (unicode, str)):
            parameters["session_schedule"] = [tuple(parameters["session_schedule"])]
    if isinstance(parameters["light_schedule"], list):
        if isinstance(parameters["light_schedule"][0], (unicode, str)):
            parameters["light_schedule"] = [tuple(parameters["light_schedule"])]

    exp = GoNoGoInterrupt(panel=panel, **parameters)
    exp.run()

    ## Testing pecking key
    from pyoperant.tlab import hwio_tlab, components_tlab
    from pyoperant.interfaces import arduino_
    from pyoperant import hwio, components
    device_name = "/dev/tty.usbmodemfd131"
    input_port = 4
    output_port = 8
    interface = arduino_.ArduinoInterface(device_name=device_name, baud_rate=19200)
    dev_input = hwio_tlab.ConfigurableBooleanInput(interface=interface,
                                                   params={"channel": input_port},
                                                   config_params={"pullup": False})
    dev_output = hwio.BooleanOutput(interface=interface,
                                    params={"channel": output_port})
    response_port = components.PeckPort(IR=dev_input, LED=dev_output, name="c")

    feeder_port = 9
    dev_feeder = hwio.BooleanOutput(interface=interface,
                                    params={"channel": feeder_port})
    feeder = components_tlab.HopperNoIR(solenoid=dev_feeder)
