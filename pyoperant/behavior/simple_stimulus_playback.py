import logging
import numpy as np
from pyoperant.behavior import base
from pyoperant.errors import EndSession
from pyoperant import utils


class SimpleStimulusPlayback(base.BaseExp):

    def __init__(self, *args, **kwargs):

        super(SimpleStimulusPlayback, self).__init__(*args, **kwargs)

        REQ_PANEL_ATTR = ["speaker",
                          "ready",
                          "idle"]

        self.req_panel_attr.extend(REQ_PANEL_ATTR)
        self.fields_to_save = ["session",
                               "index",
                               "time",
                               "stimulus_name",
                               "condition_name",
                               "intertrial_interval"]

        self.subject.create_datastore()
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
        # Wait for stimulus to finish
        utils.wait(self.this_trial.stimulus.duration)
        logger.debug("played stimulus")

    def trial_post(self):
        '''things to do at the end of a trial'''

        logger.debug("trial_post")
        if self.check_session_schedule() == False:
            logger.debug("Session has run long enough. Ending")
            raise EndSession

        # wait some random time
        if self.parameters["random_isi"] is True:
            self.this_trial.intertrial_interval = np.random.uniform(*self.parameters["isi"])
        else:
            self.this_trial.intertrial_interval = self.parameters["isi"]

        utils.wait(self.this_trial.intertrial_interval)
