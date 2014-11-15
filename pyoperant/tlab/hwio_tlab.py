from pyoperant.hwio import BooleanInput

class ConfigurableBooleanInput(BooleanInput):
    """Class which holds information about inputs and abstracts the methods of
    querying their values

    Keyword arguments:
    interface -- Interface() instance. Must have '_read_bool' method.
    params -- dictionary of keyword:value pairs needed by the interface

    Methods:
    read() -- reads value of the input. Returns a boolean
    poll() -- polls the input until value is True. Returns the time of the change
    """
    def __init__(self,interface=None,params={},config_params={},*args,**kwargs):
        super(BooleanInput, self).__init__(interface=interface,params=params,*args,**kwargs)

        assert hasattr(self.interface,'_read_bool')
        self.config(config_params)

    def config(self, config_params):
        try:
            config_params.update(self.params)
            return self.interface._config_read(**config_params)
        except AttributeError:
            return False
