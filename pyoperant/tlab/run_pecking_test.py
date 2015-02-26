#!/usr/bin/python
import os
import sys
import logging
from pyoperant import configure
from pyoperant.tlab.pecking_test import PeckingTest

box_name = sys.argv[1]

# Load config file
config_file = os.path.expanduser(os.path.join("~", "configs", "%s.yaml" % box_name))
if not os.path.exists(config_file):
    raise IOError("Config file does not exist: %s" % config_file)

if config_file.lower().endswith(".json"):
    parameters = configure.ConfigureJSON.load(config_file)
elif config_file.lower().endswith(".yaml"):
    parameters = configure.ConfigureYAML.load(config_file)

# Create experiment object
exp = PeckingTest(**parameters)
exp.run()
