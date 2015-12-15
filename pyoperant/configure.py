import os
from functools import wraps

# TODO: Do we use functools here?
# TODO: What is ConfigurableYAML?
# TODO: What is the best way to import within classes

class Configure(object):

    global_config = None

    def check(self):

        pass


class ConfigureJSON(Configure):

    global_config = None

    @classmethod
    def load(cls, config_file):
        """
        Load experiment parameters from a JSON configuration file
        :param config_file: path to a JSON configuration file
        :return: dictionary of parameters to pass to a behavior
        """
        try:
            import simplejson as json
        except ImportError:
            import json


        if cls.global_config and os.path.isfile(cls.global_config):
            with open(cls.global_config, 'rb') as config:
                parameters = json.load(config)
        else:
            parameters = dict()

        with open(config_file, 'rb') as config:
            parameters.update(json.load(config))

        return parameters

    @staticmethod
    def save(parameters, filename, overwrite=False):
        """
        Save a dictionary of parameters to an experiment JSON config file
        :param parameters: dictionary of experiment parameters
        :param filename: path to output file
        :param overwrite: whether or not to overwrite if the output file already exists
        """
        try:
            import simplejson as json
        except ImportError:
            import json

        if os.path.exists(filename) and (overwrite == False):
            raise IOError("File %s already exists! To overwrite, set overwrite=True" % filename)

        with open(filename, "w") as json_file:
            json.dump(parameters,
                      json_file,
                      sort_keys=True,
                      indent=4,
                      separators=(",", ":"))


class ConfigureYAML(Configure):

    global_config = None

    @classmethod
    def load(cls, config_file):
        """
        Load experiment parameters from a YAML configuration file
        :param config_file: path to a YAML configuration file
        :return: dictionary of parameters to pass to a behavior
        """
        import yaml

        if cls.global_config and os.path.isfile(cls.global_config):
            with open(cls.global_config, "rb") as config:
                parameters = yaml.load(config)
        else:
            parameters = dict()

        with open(config_file, "rb") as config:
            parameters.update(yaml.load(config))

        return parameters

    @staticmethod
    def save(parameters, filename, overwrite=False):
        """
        Save a dictionary of parameters to an experiment YAML config file
        :param parameters: dictionary of experiment parameters
        :param filename: path to output file
        :param overwrite: whether or not to overwrite if the output file already exists
        """
        import yaml

        if os.path.exists(filename) and (overwrite == False):
            raise IOError("File %s already exists! To overwrite, set overwrite=True" % filename)

        with open(filename, "w") as yaml_file:
            yaml.dump(parameters, yaml_file,
                      indent=4,
                      explicit_start=True,
                      explicit_end=True)


## What is this??
class ConfigurableYAML(type):

    def __new__(cls, *args, **kwargs):

        ConfigureYAML.constructors.append(cls)
        return super(ConfigureableYAML, cls, *args, **kwargs)
