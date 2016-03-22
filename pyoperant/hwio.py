import logging

logger = logging.getLogger(__name__)


class BaseIO(object):
    """Any type of IO device. Maintains info on the interface and configuration
    params for querying the IO device"""

    def __init__(self, name=None, interface=None, params={},
                 *args, **kwargs):

        self.name = name
        self.interface = interface
        self.params = params


class BooleanInput(BaseIO):
    """Class which holds information about inputs and abstracts the methods of
    querying their values

    Keyword arguments:
    interface -- Interface() instance. Must have '_read_bool' method.
    params -- dictionary of keyword:value pairs needed by the interface to
    configure and read from the device.

    Methods:
    read() -- reads value of the input. Returns a boolean
    poll() -- polls the input until value is True. Returns the time of the change
    """

    def __init__(self, interface=None, params={},
                 *args, **kwargs):
        super(BooleanInput, self).__init__(interface=interface,
                                           params=params,
                                           *args,
                                           **kwargs)

        assert hasattr(self.interface, '_read_bool')
        self.config()

    def config(self):
        """
        Calls the interfaces _config_read method with the keyword arguments
        in params
        """

        # This should be handled by the assert statement, right?
        try:
            return self.interface._config_read(**self.params)
        except AttributeError:
            return False

    def read(self):
        """
        Read the status of the boolean input
        """

        return self.interface._read_bool(**self.params)

    def poll(self, timeout=None):
        """ Runs a loop, querying for the boolean input to return True.
        :returns peck time or "GoodNite" exception
        """
        if hasattr(self.interface, "poll"):
            return self.interface._poll(timeout=timeout, **self.params)



class BooleanOutput(BaseIO):
    """Class which holds information about outputs and abstracts the methods of
    writing to them

    Keyword arguments:
    interface -- Interface() instance. Must have '_write_bool' method.
    params -- dictionary of keyword:value pairs needed by the interface

    Methods:
    write(value) -- writes a value to the output. Returns the value
    read() -- if the interface supports '_read_bool' for this output, returns
        the current value of the output from the interface. Otherwise this
        returns the last passed by write(value)
    toggle() -- flips the value from the current value
    """
    def __init__(self,interface=None,params={},*args,**kwargs):
        super(BooleanOutput, self).__init__(interface=interface,params=params,*args,**kwargs)

        assert hasattr(self.interface,'_write_bool')
        self.last_value = None
        self.config()


    def config(self):
        try:
            logger.debug("Configuring BooleanOutput to write on interface % s" % self.interface)
            return self.interface._config_write(**self.params)
        except AttributeError:
            logger.debug("Interface %s has not _config_write method" % self.interface)
            return False

    def read(self):
        """read status"""
        if hasattr(self.interface,'_read_bool'):
            value = self.interface._read_bool(**self.params)
            logger.debug("Current value reported as %s" % value)
            return value
        else:
            logger.debug("Current value set as %s" % value)
            return self.last_value

    def write(self,value=False):
        """write status"""
        logger.debug("Setting value to %s" % value)
        self.last_value = self.interface._write_bool(value=value,**self.params)
        return self.last_value

    def toggle(self):
        value = not self.read()
        return self.write(value=value)

class AudioOutput(BaseIO):
    """Class which holds information about audio outputs and abstracts the
    methods of writing to them

    Keyword arguments:
    interface -- Interface() instance. Must have the methods '_queue_wav',
        '_play_wav', '_stop_wav'
    params -- dictionary of keyword:value pairs needed by the interface

    Methods:
    queue(wav_filename) -- queues
    read() -- if the interface supports '_read_bool' for this output, returns
        the current value of the output from the interface. Otherwise this
        returns the last passed by write(value)
    toggle() -- flips the value from the current value
    """

    def __init__(self, interface=None, params={}, *args, **kwargs):
        super(AudioOutput, self).__init__(interface=interface,
                                          params=params,
                                          *args,
                                          **kwargs)

        assert hasattr(self.interface,'_queue_wav')
        assert hasattr(self.interface,'_play_wav')
        assert hasattr(self.interface,'_stop_wav')
        self.config()

    def config(self):

        if hasattr(self.interface, '_config_write'):
            self.interface._config_write(**self.params)

    def queue(self,wav_filename):
        return self.interface._queue_wav(wav_filename)

    def play(self):
        return self.interface._play_wav()

    def stop(self):
        return self.interface._stop_wav()
