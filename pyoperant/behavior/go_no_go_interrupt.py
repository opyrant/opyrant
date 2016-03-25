#!/usr/bin/env python
import os
import sys
import logging
import csv
import datetime as dt
import random
import numpy as np
from pyoperant.behavior import base
from pyoperant.errors import EndSession
from pyoperant import states, trials, blocks
from pyoperant import components, utils, reinf, queues, configure, stimuli, subjects

logger = logging.getLogger(__name__)

# TODO: Document classes and experiment methods
# TODO: What do the classes override? What do they inherit and why?

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
        self.subject.create_datastore()
        self.start_immediately = False
        self.session_id = 0

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

if __name__ == "__main__":

    # Load config file
    config_file = "/path/to/config"
    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    # Create experiment object
    exp = GoNoGoInterrupt(**parameters)
    exp.run()
