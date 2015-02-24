#!/usr/local/bin/python
import os
import sys
import logging
import csv
import datetime as dt
import random
import numpy as np
from pyoperant.behavior import base
from pyoperant.errors import EndSession
from pyoperant.experiment import states, trials
from pyoperant import components, utils, reinf, queues, configure, stimuli, subjects

logger = logging.getLogger(__name__)

class RewardedCondition(stimuli.StimulusConditionWav):

    def __init__(self, file_path="", recursive=False):

        super(RewardedCondition, self).__init__(name="Rewarded",
                                                response=False,
                                                is_rewarded=True,
                                                file_path=file_path,
                                                recursive=recursive)


class UnrewardedCondition(stimuli.StimulusConditionWav):

    def __init__(self, file_path="", recursive=False):

        super(UnrewardedCondition, self).__init__(name="Unrewarded",
                                                  response=True,
                                                  file_path=file_path,
                                                  recursive=recursive)

class GoNoGoInterrupt(base.BaseExp):
    """A go no-go interruption experiment

    Required Parameters
    ----------
    name
    desc
    subject
    debug
    experiment_path
    session_schedule
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



    # Default configuration values until we figure out a way to properly handle
    # and merge configurations. Currently without a strongly enforced config file
    # structure, being flexible with these parameters gets very challenging. If
    # these need to be changed in the meantime, just subclass this class and change
    # them. I've set them here so that can be done easily.
    _RewardedCondition = RewardedCondition
    _UnrewardedCondition = UnrewardedCondition
    _Reinforcement = reinf.ContinuousReinforcement
    _trial_queue = queues.random_queue
    _block_queue = queues.block_queue

    def __init__(self, *args, **kwargs):

        super(GoNoGoInterrupt,  self).__init__(*args, **kwargs)

        REQ_PANEL_ATTR = ["speaker",
                          "response_port",
                          "reward",
                          "ready",
                          "idle"]

        self.req_panel_attr.extend(REQ_PANEL_ATTR)
        self.fields_to_save = ['session',
                               'index',
                               'time',
                               'stimulus_name',
                               'condition_name',
                               'response',
                               'correct',  # redundant
                               'rt',
                               'reward',  # redundant
                               'max_wait',
                               ]

        # Create a subject object
        logger.info("Creating subject object for %s" % self.parameters["subject"])
        self.subject = subjects.Subject(name=self.parameters["subject"], datastore="csv", output_path=self.parameters["experiment_path"], experiment=self)

        # Create block designs and stimulus conditions. Could any of this go in base?
        self.block_designs = list()
        # This gets incredibly complicated without requiring some level of consistency in the logs
        # Do that, please. Some of this could be done in the block initialization.
        if "blocks" in self.parameters:
            for block_params in self.parameters["blocks"]:
                block_design = trials.Block()
                block_design.experiment = self
                block_design.max_trials = block_params.get("max_trials", None)
                block_design.queue = block_params.get("queue", self._trial_queue)
                block_design.queue_parameters = block_params.get("queue_parameters", {})
                if "reinforcement" in block_params:
                    block_design.reinforcement = block_params["reinforcement"]
                elif "reinforcement" in self.parameters:
                    block_design.reinforcement = self.parameters["reinforcement"]
                else:
                    block_design.reinforcement = self._Reinforcement()

                if isinstance(block_design.reinforcement, str):
                    try:
                        block_design.reinforcement = reinf.SCHEDULE_DICT[block_design.reinforcement]()
                    except KeyError:
                        raise KeyError("Unknown value for reinforcement: %s. Known values are: %s" % (block_design.reinforcement, ", ".join(reinf.SCHEDULE_DICT.keys())))

                if "conditions" in block_params:
                    weights = list()
                    condition_params = block_params["conditions"]["rewarded"]
                    file_path = condition_params.get("file_path", os.path.join(self.parameters["stim_path"], "reward"))
                    weights.append(condition_params.get("weight", 0.5))
                    rewarded_stimuli = RewardedCondition(file_path=file_path)

                    condition_params = block_params["conditions"]["unrewarded"]
                    file_path = condition_params.get("file_path", os.path.join(self.parameters["stim_path"], "reward"))
                    weights.append(condition_params.get("weight", 0.5))
                    unrewarded_stimuli = UnrewardedCondition(file_path=file_path)

                    block_design.conditions = [rewarded_stimuli, unrewarded_stimuli]
                    block_design.weights = weights

                self.block_designs.append(block_design)

        self.session_id = 0

    def shape(self):
        """
        This will house a method to run shaping.
        """

        pass

    ## Session Flow
    def session_pre(self):
        """ Runs before the session starts
        """
        logger.debug("Beginning session")
        self.session_id += 1
        self.session_start_time = dt.datetime.now()

    def session_main(self):
        """ Runs the sessions
        """

        # What we want!
        # How to handle configuration?? Currently this is predefined
        queue = self.parameters.get("block_queue", self._block_queue)
        queue_parameters = self.parameters.get("block_queue_parameters", dict())
        self.blocks = queues.BlockHandler(queue=queue, blocks=self.block_designs, queue_parameters=queue_parameters)
        for self.this_block in self.blocks:
            logger.info("Beginning block #%d" % self.this_block.index)
            self.panel.ready()
            self.start_immediately = False
            for trial in queues.TrialHandler(self.this_block):
                trial.run()

    def trial_pre(self):
        ''' this is where we initialize a trial'''
        logger.debug("Starting trial #%d" % self.this_trial.index)
        # Store trial data
        self.this_trial.session = self.session_id
        self.this_trial.annotate(stimulus_name=self.this_trial.stimulus.file_origin,
                                 condition_name=self.this_trial.condition.name,
                                 max_wait=self.this_trial.stimulus.duration,
                                 )
        if not self.start_immediately:
            logger.debug("Begin polling for a response")
            self.panel.response_port.poll()
            if (self.this_trial.index == 1) and ("session_duration" in self.parameters):
                self.schedule_current_session()


    def stimulus_pre(self):
        # wait for bird to peck
        logger.debug("stimulus_pre - queuing file in speaker")
        self.panel.speaker.queue(self.this_trial.stimulus.file_origin)
        logger.debug("wavfile queued")

    def stimulus_main(self):
        ##play stimulus
        logger.debug("stimulus_main")
        self.this_trial.time = dt.datetime.now()
        logger.info("Trial %d - %s - %s - %s" % (self.this_trial.index,
                                                   self.this_trial.time.strftime("%H:%M:%S"),
                                                   self.this_trial.condition.name,
                                                   self.this_trial.stimulus.name))
        # ipdb.set_trace()
        self.panel.speaker.play() # already queued in stimulus_pre()
        logger.debug("played stimulus")

    def response_main(self):

        logger.debug("response_main")

        self.this_trial.response_time = self.panel.response_port.poll(self.this_trial.stimulus.duration)
        logger.debug("Received peck or timeout. Stopping playback")

        self.panel.speaker.stop()
        logger.debug("Playback stopped")

        if self.this_trial.response_time is None:
            self.this_trial.response = 0
            self.start_immediately = False # Next trial will poll for a response before beginning
            self.this_trial.rt = np.nan
        else:
            self.this_trial.response = 1
            self.start_immediately = True # Next trial will begin immediately
            self.this_trial.rt = self.this_trial.response_time - self.this_trial.time

    def consequate_main(self):

        # This is maybe a bit overly done
        if self.this_trial.response == self.this_trial.condition.response:
            self.this_trial.correct = True
            if self.this_trial.condition.is_rewarded:
                if self.this_block.reinforcement.consequate(self.this_trial):
                    self.reward()
        else:
            self.this_trial.correct = False
            if self.this_trial.condition.is_punished:
                if self.this_block.reinforcement.consequate(self.this_trial):
                    self.punish()

    def reward(self):

        self.this_trial.reward = True
        logger.debug("reward_main")
        value = self.parameters['reward_value']
        logger.info("Supplying reward for %3.2f seconds" % value)
        reward_event = self.panel.reward(value=value)
        if isinstance(reward_event, dt.datetime): # There was a response during the reward period
            self.start_immediately = True

    def trial_post(self):
        '''things to do at the end of a trial'''

        logger.debug("trial_post")
        if self.check_session_schedule() == False:
            logger.debug("Session has run long enough. Ending")
            raise EndSession

    def session_post(self):
        """ Closes out the sessions
        """

        self.session_end_time = dt.datetime.now()
        logger.info("Finishing session %d at %s" % (self.session_id, self.session_end_time.ctime()))
        if self.session_id < self.parameters.get("num_sessions", 1):
            self.schedule_next_session()
        else:
            logger.info("Finished all sessions.")


if __name__ == "__main__":

    from pyoperant.tlab.local_tlab import PANELS
    # Load config file
    logging.basicConfig(level=logging.INFO)
    config_file = "/home/tlee/Data/code/pyoperant/pyoperant/tlab/go_no_go_interrupt_config.yaml"
    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    # Create panel object
    panel = PANELS[parameters["panel_name"]]()

    # Create experiment object
    exp = GoNoGoInterrupt(panel=panel, **parameters)
    exp.run()
