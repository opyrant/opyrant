#!/usr/local/bin/python
import os
import logging
import datetime as dt
from pyoperant import configure
from pyoperant import stimuli
from pyoperant.tlab.polling_filter import PollingFilter, AudioPlaybackFilter
from pyoperant.behavior.go_no_go_interrupt import GoNoGoInterrupt

logger = logging.getLogger(__name__)

class ProbeCondition(stimuli.NonrandomStimulusConditionWav):

    def __init__(self, file_path="", recursive=False):

        super(ProbeCondition, self).__init__(name="Probe",
                                             response=False,
                                             is_rewarded=False,
                                             file_path=file_path,
                                             recursive=recursive)

class PeckingTest(GoNoGoInterrupt):
    # Additional configurations:
    # log_polling = (True / False)
    # log_polling_file = (filename)
    # log_playback = (True / False)
    # log_playback_file = (filename)

    def __init__(self, *args, **kwargs):

        super(PeckingTest, self).__init__(*args, **kwargs)

        if self.parameters.get("log_polling", False):
            self.config_polling_log()
        if self.parameters.get("log_playback", False):
            self.config_playback_log()

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

    def config_playback_log(self):

        if "log_playback_file" in self.parameters:
            filename = os.path.join(self.parameters["experiment_path"],
                                    self.parameters["log_playback_file"])
        else:
            filename = os.path.join(self.parameters["experiment_path"],
                                    "audio_playback.log")

        playback_handler = logging.FileHandler(filename)
        playback_handler.setLevel(logging.DEBUG)
        playback_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        playback_filter = AudioPlaybackFilter()
        playback_handler.addFilter(playback_filter)

        logger = logging.getLogger("pyoperant.interfaces.pyaudio_")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(playback_handler)

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


def run_pecking_test(args):

    print "Called run_pecking_test"
    box_name = "Box%d" % args.box
    config_dir = os.path.expanduser(os.path.join("~", "Dropbox", "pecking_test", "configs"))

    # Load config file
    if args.config is not None:
        if os.path.exists(args.config):
            config_file = args.config
        elif os.path.exists(os.path.join(config_dir, args.config)):
            config_file = os.path.join(config_dir, args.config)
        else:
            raise IOError("Config file %s could not be found" % args.config)
    else:
        config_file = os.path.join(config_dir, "%s.yaml" % box_name)

    if not os.path.exists(config_file):
        raise IOError("Config file does not exist: %s" % config_file)

    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    # Modify the bird name

    # Modify the experimenter name

    # Modify the output directory

    parameters["experiment_path"] = os.path.join(parameters["experiment_path"],
                                                 parameters["subject"].name,
                                                 dt.datetime.now().strftime("%d%m%y"))

    if not os.path.exists(parameters["experiment_path"]):
        os.makedirs(parameters["experiment_path"])

    # Set up a helpful symbolic link in the home directory
    data_link = os.path.expanduser(os.path.join("~", "data_%s" % box_name))
    if os.path.exists(data_link):
        os.remove(data_link)
    os.symlink(parameters["experiment_path"], data_link)

    # Create experiment object
    exp = PeckingTest(**parameters)
    exp.run()


if __name__ == "__main__":
    import sys

    box_name = sys.argv[1]
    config_dir = os.path.expanduser(os.path.join("~", "Dropbox", "pecking_test", "configs"))

    # Load config file
    config_file = os.path.join(config_dir, "%s.yaml" % box_name)
    if not os.path.exists(config_file):
        raise IOError("Config file does not exist: %s" % config_file)

    if config_file.lower().endswith(".json"):
        parameters = configure.ConfigureJSON.load(config_file)
    elif config_file.lower().endswith(".yaml"):
        parameters = configure.ConfigureYAML.load(config_file)

    parameters["experiment_path"] = os.path.join(parameters["experiment_path"],
                                                 parameters["subject"].name,
                                                 dt.datetime.now().strftime("%d%m%y"))

    if not os.path.exists(parameters["experiment_path"]):
        os.makedirs(parameters["experiment_path"])

    data_link = os.path.expanduser(os.path.join("~", "data_%s" % box_name))
    if os.path.exists(data_link):
        os.remove(data_link)
    os.symlink(parameters["experiment_path"], data_link)

    # Create experiment object
    exp = PeckingTest(**parameters)
    exp.run()
