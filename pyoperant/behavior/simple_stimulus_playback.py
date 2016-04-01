import logging
import numpy as np
from pyoperant.behavior import base
from pyoperant.errors import EndSession
from pyoperant import utils


class SimpleStimulusPlayback(base.BaseExp):

    req_panel_attr = ["sleep",
                      "reset",
                      "idle",
                      "ready",
                      "speaker"]

    fields_to_save = ['session',
                      'index',
                      'time',
                      'stimulus_name',
                      'condition_name',
                      'intertrial_interval']

    def trial_pre(self):
        """ Store data that is specific to this experiment, and compute a wait time for an intertrial interval
        """
        stimulus = self.this_trial.stimulus.file_origin
        condition = self.this_trial.condition.name
        if isinstance(self.parameters["intertrial_interval"], (list, tuple)):
            iti = np.random.uniform(*self.parameters["intertrial_interval"])
        else:
            iti = self.parameters["intertrial_interval"]

        self.this_trial.annotate(stimulus_name=stimulus,
                                 condition_name=condition,
                                 intertrial_interval=iti)
        utils.wait(iti)

    def stimulus_main(self):

        self.panel.speaker.queue(self.this_trial.stimulus.file_origin)
        self.this_trial.time = dt.datetime.now()
        self.panel.speaker.play()
        # Wait for stimulus to finish
        utils.wait(self.this_trial.stimulus.duration)

    def trial_post(self):
        '''things to do at the end of a trial'''

        # This can probably go in the trial.run()

        if self.check_session_schedule() is False:
            logger.debug("Session has run long enough. Ending")
            raise EndSession
