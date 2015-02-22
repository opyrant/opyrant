import os


class Configure(object):

    global_config = None

    def check(self):

        pass

class ConfigureJSON(Configure):

    global_config = None

    @classmethod
    def load(cls, config_file):
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
        import yaml

        if os.path.exists(filename) and (overwrite == False):
            raise IOError("File %s already exists! To overwrite, set overwrite=True" % filename)

        with open(filename, "w") as yaml_file:
            yaml.dump(parameters, yaml_file,
                      indent=4,
                      explicit_start=True,
                      explicit_end=True)
