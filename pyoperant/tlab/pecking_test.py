#!/usr/bin/env python
import os
import logging
import datetime as dt
from pyoperant import configure
from pyoperant import stimuli
from pyoperant.tlab.logging import PollingFilter, AudioPlaybackFilter
from pyoperant.behavior.go_no_go_interrupt import GoNoGoInterrupt
from pyoperant.tlab import local_tlab

logger = logging.getLogger(__name__)


class ProbeCondition(stimuli.StimulusConditionWav):
    """ Probe stimuli are not consequated and should be sampled as evenly as
    possible. This is done by setting replacement to False and shuffle to True.
    """

    def __init__(self, name="Probe",
                 response=False,
                 is_rewarded=False,
                 is_punished=False,
                 replacement=False,
                 shuffle=True,
                 *args, **kwargs):

        super(ProbeCondition, self).__init__(name=name,
                                             response=response,
                                             is_rewarded=is_rewarded,
                                             is_punished=is_punished,
                                             replacement=replacement,
                                             shuffle=shuffle,
                                             *args, **kwargs)

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
        """
        We don't use any session scheduling, so always return True.
        """

        return True

    def check_light_schedule(self):
        """
        We don't run experiments based on light-dark schedules, so always return True.
        """

        return True

    def save(self):
        """
        Save the experiment parameters
        """

        self.snapshot_f = os.path.join(self.parameters["experiment_path"],
                                       "configuration.yaml")
        logger.debug("Saving configurations as %s" % self.snapshot_f)
        configure.ConfigureYAML.save(self.parameters,
                                     self.snapshot_f,
                                     overwrite=True)

    def reward(self):
        """
        Custom reward method to put the feeder up during the reward period but still respond to pecks. If the key is pecked, the next trial begins immediately.
        :return:
        """

        self.this_trial.reward = True
        logger.debug("reward_main")
        value = self.parameters['reward_value']
        logger.info("Supplying reward for %3.2f seconds" % value)
        reward_event = self.panel.reward(value=value)
        if isinstance(reward_event, dt.datetime): # There was a response during the reward period
            self.this_trial.reward = False # maybe use reward_event here instead?
            self.start_immediately = True


def run_pecking_test(args):
    """
    Start a new pecking test and run it using the modifications provided by args.
    """

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
    else:
        raise ValueError("Currently only .yaml and .json configuration files are allowed")

    # The panel is specified by args.box
    parameters["panel"] = getattr(local_tlab, "Box%d" % args.box)()

    # Modify the bird name
    if args.bird is not None:
        parameters["subject"].name = args.bird

    # Modify the experimenter name
    if args.experimenter is not None:
        parameters["experimenter"]["name"] = args.experimenter

    # Modify the output directory
    if args.outputdir is not None:
        parameters["experiment_path"] = os.path.join(args.outputdir,
                                                     parameters["subject"].name,
                                                     dt.datetime.now().strftime("%d%m%y"))
    else:
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
    import argparse
    from pyoperant import subjects
    from pyoperant.tlab import local_tlab

    run_parser = argparse.ArgumentParser("run", description="Run a pecking test experiment")
    run_parser.add_argument("box", help="Which box to run (e.g. 5)")
    run_parser.add_argument("-c", "--config",
                            dest="config",
                            help="Path to a config file. Default /home/fet/Dropbox/configs/Box#.yaml")
    run_parser.add_argument("-b", "--bird",
                            dest="bird",
                            help="Name of the subject. Default specified in config file")
    run_parser.add_argument("-e", "--experimenter",
                            dest="experimenter",
                            help="Name of the experimenter. Default specified in config file")
    # run_parser.add_argument("-s", "--stimdir",
    #                         dest="stimdir",
    #                         help="Stimulus directory. Default specified in config file")
    run_parser.add_argument("-o", "--outputdir",
                            dest="outputdir",
                            help="Data output directory. Default specified in  config file")

    args = run_parser.parse_args()
    run_pecking_test(args)
