#!/usr/local/bin/python

import os
import sys
import logging
import csv
import datetime as dt
import random
# import ipdb
from pyoperant.behavior import base, shape
from pyoperant.errors import EndSession
from pyoperant import components, utils, reinf, queues, configure


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

    REQ_PANEL_ATTRS = ["speaker",
                      "response_port",
                       "reward",
                       "ready",
                       "idle"]

    def __init__(self, *args, **kwargs):

        super(GoNoGoInterrupt,  self).__init__(*args, **kwargs)

        self.req_panel_attrs.extend(self.REQ_PANEL_ATTRS)
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
        self.log.info("Creating subject object for %s" % self.parameters["subject"])
        self.subject = Subject(name=self.parameters["subject"], datastore="csv", output_path="/path/to/datastore")

        # Create block designs and stimulus conditions. Could any of this go in base?
        self.block_designs = list()
        # This gets incredibly complicated without requiring some level of consistency in the logs
        # Do that, please.
        if "blocks" in self.parameters:
            for block_params in self.parameters["blocks"]:
                block_design = Block()
                block_design.max_trials = block_params.get("max_trials", None)
                block_design.queue = block_params.get("queue", queues.random_queue)
                block_design.queue_parameters = block_params.get("queue_parameters", {})
                if "reinforcement" in block_params:
                    block_design.reinforcement = reinforcement
                elif "reinforcement" in self.parameters:
                    block_design.reinforcement = reinforcement
                else:
                    block_design.reinforcement = reinf.ContinuousReinforcement()

                if isinstance(block_design.reinforcement, str):
                    try:
                        block_design.reinforcement = reinf.SCHEDULE_DICT[block_design.reinforcement]
                    except KeyError:
                        raise KeyError("Unknown value for reinforcement: %s. Known values are: %s" (block_design.reinforcement, ", ".join(reinf.SCHEDULE_DICT.keys())))

                if "conditions" in block_params:
                    weights = list()
                    condition_params = block_params["conditions"]["rewarded"]
                    file_path = condition_params.get("file_path", os.path.join(self.stim_path, "reward"))
                    weights.append(condition_params.get("weight", 0.5))
                    rewarded_stimuli = RewardedCondition(file_path=file_path)

                    condition_params = block_params["conditions"]["unrewarded"]
                    file_path = condition_params.get("file_path", os.path.join(self.stim_path, "reward"))
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
        self.log.debug("Beginning session")

    def session_main(self):
        """ Runs the sessions
        """

        # What we want!
        # How to handle configuration?? Currently this is predefined
        queue = self.parameters.get("block_queue", queues.block_queue)
        queue_parameters = self.parameters.get("block_queue_parameters", dict())
        self.blocks = BlockHandler(queue=queue, blocks=self.block_designs, queue_parameters=queue_parameters)
        for self.this_block in self.blocks:            
            self.log.info("Beginning block #%d" % self.this_block.index)
            self.panel.ready()
            self.start_immediately = False
            for trial in TrialHandler(self.this_block):
                trial.run()


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

    def trial_pre(self):
        ''' this is where we initialize a trial'''
        self.log.debug("Starting trial #%d" % self.this_trial.index)
        if not self.start_immediately:
            self.log.debug("Begin polling for a response")
            self.response_port.poll()

    def stimulus_pre(self):
        # wait for bird to peck
        self.log.debug("stimulus_pre - queuing file in speaker")
        self.panel.speaker.queue(self.this_trial.stimulus.file_origin)
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

    def response_post(self):

        pass

    def consequate_pre(self):

        pass

    def consequate_main(self):

        # This is maybe a bit overly done
        if self.this_trial.response == self.this_trial.condition.response:
            self.this_trial.correct = True
            if self.this_trial.condition.is_rewarded:
                if self.reinforcement.consequate(self.this_trial):
                    self.reward()
        else:
            self.this_trial.correct = False
            if self.this_trial.condition.is_punished:
                if self.reinforcement.consequate(self.this_trial):
                    self.punish()

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

        if self.check_session_schedule()==False:
            self.log.debug("Session has run long enough. Ending")
            raise EndSession

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


class RewardedCondition(StimulusConditionWav):

    def __init__(self, file_path="", recursive=False):

        super(RewardedCondition, self).__init__(name="Rewarded",
                                                response=False,
                                                is_rewarded=True,
                                                file_path=file_path,
                                                recursive=recursive)


class UnrewardedCondition(StimulusConditionWav):

    def __init__(self, file_path="", recursive=False):

        super(UnrewardedCondition, self).__init__(name="Unrewarded",
                                                  response=True,
                                                  file_path=file_path,
                                                  recursive=recursive)


if __name__ == "__main__":

    # Load config file
    config_file = "/Users/tylerlee/code/pyoperant/pyoperant/tlab/go_no_go_interrupt_config.yaml"
    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    # Create panel object
    panel = PANELS[parameters['panel']]()

    # Create experiment object
    exp = GoNoGoInterrupt(panel=panel, **parameters)
    exp.run()
