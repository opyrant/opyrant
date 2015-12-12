#!/usr/bin/python
import os
import sys
import logging
import datetime as dt
from pyoperant import configure
from pyoperant.tlab.pecking_test import PeckingTest

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
