#!/usr/bin/python
import os
import logging
from pyoperant.tlab.local_tlab import PANELS
from pyoperant.tlab.polling_filter import PollingFilter
from pyoperant.behavior.go_no_go_interrupt import *


# Load config file
logging.basicConfig(level=logging.INFO)
config_file = "/home/tlee/Data/code/pyoperant/pyoperant/tlab/pecking_test_config.yaml"
if config_file.lower().endswith(".json"):
    parameters = configure.ConfigureJSON.load(config_file)
elif config_file.lower().endswith(".yaml"):
    parameters = configure.ConfigureYAML.load(config_file)

# Create panel object
panel = PANELS[parameters["panel_name"]]()

# Create experiment object
exp = GoNoGoInterrupt(panel=panel, **parameters)
polling_file = os.path.join(exp.parameters["experiment_path"], "keydata.txt")
polling_handler = logging.FileHandler(polling_file)
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

exp.run()
