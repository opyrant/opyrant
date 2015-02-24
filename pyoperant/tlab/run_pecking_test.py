#!/usr/bin/python
import os
import sys
import logging
from pyoperant.tlab.local_tlab import PANELS
from pyoperant.tlab.polling_filter import PollingFilter
from pyoperant.tlab.pecking_test import PeckingTest

box_name = sys.argv[1]
if box_name not in PANELS:
    raise Exception("First argument must be the box name (e.g. Box2)")

# Load config file
config_file = os.path.expanduser(os.path.join("~", "configs", "%s.yaml" % box_name))
if not os.path.exists(config_file):
    raise IOError("Config file does not exist: %s" % config_file)

if config_file.lower().endswith(".json"):
    parameters = configure.ConfigureJSON.load(config_file)
elif config_file.lower().endswith(".yaml"):
    parameters = configure.ConfigureYAML.load(config_file)

# Create panel object
panel = PANELS[box_name]()

# Create experiment object
exp = PeckingTest(panel=panel, **parameters)
exp.run()
