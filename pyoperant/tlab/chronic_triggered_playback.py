import logging
import numpy as np
from pyoperant.tlab.chronic_playback import ChronicPlayback
from pyoperant import utils


logger = logging.getLogger(__name__)

class ChronicTriggeredPlayback(ChronicPlayback):
        """ Theunissen lab simple button-triggered playback experiment.
        For documentation of arguments see behavior.base.BaseExp and
        behavior.simple_stimulus_playback.SimpleStimulusPlayback
        """

        def trial_pre(self):
            """ Store data that is specific to this experiment, and compute a wait time for an intertrial interval
            """

            stimulus = self.this_trial.stimulus.file_origin
            if isinstance(self.intertrial_interval, (list, tuple)):
                iti = np.random.uniform(*self.intertrial_interval)
            else:
                iti = self.intertrial_interval

            logger.debug("Waiting for %1.3f seconds" % iti)
            self.this_trial.annotate(stimulus_name=stimulus,
                                     intertrial_interval=iti)
            utils.wait(iti)

            self.panel.button.poll()
