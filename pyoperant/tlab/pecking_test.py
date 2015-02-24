#!/usr/local/bin/python
import os
import logging
import datetime as dt
from pyoperant import configure
from pyoperant.tlab.local_tlab import PANELS
from pyoperant.tlab.polling_filter import PollingFilter
from pyoperant.behavior.go_no_go_interrupt import GoNoGoInterrupt

logger = logging.getLogger(__name__)

class PeckingTest(GoNoGoInterrupt):
    # Additional configurations:
    # log_polling = (True / False)
    # log_polling_file = (filename)

    def __init__(self, *args, **kwargs):

        kwargs["experiment_path"] = os.path.join(kwargs["experiment_path",
                                                 kwargs["subject"],
                                                 dt.datetime.now().strftime("%d%m%y"))

        super(PeckingTest, self).__init__(*args, **kwargs)

        if self.parameters.get("log_polling", False):
            self.config_polling_log()

    def config_polling_log(self):

        if "log_polling_file" in self.parameters:
            filename = os.path.join(self.parameters["experiment_path"],
                                    self.parameters["log_polling_file"])
        else:
            filename = os.path.join(self.parameters["experiment_path"],
                                    "keydata.log")

        polling_handler = logging.FileHandler(filename)
        polling_handler.setLevel(logging.DEBUG)
        polling_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        polling_filter = PollingFilter()
        polling_handler.addFilter(polling_filter)

        logger = logging.getLogger("pyoperant.interfaces.arduino_")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(polling_handler)

        logger = logging.getLogger()
        for handler in logger.handlers:
            if handler.level < logger.level:
                handler.setLevel(logger.level)

    def check_session_schedule(self):

        return True

    def check_light_schedule(self):

        return True

    def save(self):

        self.snapshot_f = os.path.join(self.parameters["experiment_path"],
                                       "configuration.yaml")
        logger.debug("Saving configurations as %s" % self.snapshot_f)
        configure.ConfigureYAML.save(self.parameters,
                                     self.snapshot_f,
                                     overwrite=True)

    def reward(self):

        self.this_trial.reward = True
        logger.debug("reward_main")
        value = self.parameters['reward_value']
        logger.info("Supplying reward for %3.2f seconds" % value)
        reward_event = self.panel.reward(value=value)
        if isinstance(reward_event, dt.datetime): # There was a response during the reward period
            self.this_trial.reward = False # maybe use reward_event here instead?
            self.start_immediately = True


if __name__ == "__main__":
    import sys

    box_name = sys.argv[1]
    if box_name not in PANELS:
        raise Exception("First argument must be the box name (e.g. Box2)")

    # Load config file
    config_file = os.path.expanduser(os.path.join("~", "configs", "%s.yaml" % box_name))
    if not os.path.exists(config_file):
        raise IOError("Config file does not exist: %s" % config_file)

    logging.basicConfig(level=logging.INFO)
    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    # Create panel object
    panel = PANELS[parameters["panel_name"]]()

    # Create experiment object
    exp = PeckingTest(panel=panel, **parameters)
    exp.run()
