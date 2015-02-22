import time
import datetime
import serial
import logging
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError

logger = logging.getLogger(__name__)

class ArduinoInterface(base_.BaseInterface):
    """Creates a pyserial interface to communicate with an arduino via the serial connection.
    Communication is through two byte messages where the first byte specifies the channel and the second byte specifies the action.
    Valid actions are:
    0. Read input value
    1. Set output to ON
    2. Set output to OFF
    3. Sets channel as an output
    4. Sets channel as an input
    5. Sets channel as an input with a pullup resistor (basically inverts the input values)
    :param device_name: The address of the device on the local system (e.g. /dev/tty.usbserial)
    :param baud_rate: The baud rate for serial communication
    TODO: Raise reasonable exceptions.
    TODO:
    """
    def __init__(self, device_name, baud_rate=9600, inputs=None, outputs=None, *args, **kwargs):

        super(ArduinoInterface, self).__init__(*args, **kwargs)

        self.device_name = device_name
        self.baud_rate = baud_rate
        self.device = None

        self.read_params = ('channel', 'pullup')
        self._state = dict()
        self.inputs = []
        self.outputs = []

        self.open()
        if inputs is not None:
            for input_ in inputs:
                self._config_read(*input_)
        if outputs is not None:
            for output in outputs:
                self._config_write(output)

    def __str__(self):

        return "Arduino device at %s: %d input channels and %d output channels configured" % (self.device_name, len(self.inputs), len(self.outputs))

    def __repr__(self):

        return "ArduinoInterface(%s, baud_rate=%d)" % (self.device_name, self.baud_rate)

    def open(self):
        '''Open a serial connection for the device
        :return: None
        '''

        self.device = serial.Serial(self.device_name, self.baud_rate)
        if self.device is None:
            raise InterfaceError('Could not open serial device %s' % self.device_name)
        utils.wait(1.5)
        self.device.readline() # This line ensures that the device has initialized, but for some reason it takes much longer on linux than osx


    def close(self):
        '''Close a serial connection for the device
        :return: None
        '''

        self.device.close()

    def _config_read(self, channel, pullup=False):
        ''' Configure the channel to act as an input
        :param channel: the channel number to configure
        :param pullup: the channel should be configured in pullup mode. On the arduino this has the effect of
        returning HIGH when unpressed and LOW when pressed. The returned value will have to be inverted.
        :return: None
        '''

        if pullup is False:
            self.device.write(self._make_arg(channel, 4))
        else:
            self.device.write(self._make_arg(channel, 5))

        if channel in self.outputs:
            self.outputs.remove(channel)
        if channel not in self.inputs:
            self.inputs.append(channel)

        self._state[channel] = dict(invert=pullup, pressed=False)

    def _config_write(self, channel):
        ''' Configure the channel to act as an output
        :param channel: the channel number to configure
        :return: None
        '''

        self.device.write(self._make_arg(channel, 3))
        if channel in self.inputs:
            self.inputs.remove(channel)
        if channel not in self.outputs:
            self.outputs.append(channel)

    def _read_bool(self, channel):
        ''' Read a value from the specified channel
        :param channel: the channel from which to read
        :return: value
        TODO: Is the comment on hanging necessary? Define my own error for any problems.
        '''

        self.device.write(self._make_arg(channel, 0))
        v = ord(self.device.read())  # Read hangs until the values are read. Not sure how to work with this
        if v in [0, 1]:
            try:
                if self._state[channel]["invert"]:
                    v = 1 - v
                return v == 1
            except KeyError:  # This channel has not been configured!
                raise InterfaceError('Channel %d of device %s has not yet been configured!' % (channel, self.device))
        else:
            raise InterfaceError('Could not read from serial device "%s", channel %d' % (self.device, channel))

    def _poll(self, channel, timeout=None):
        """ runs a loop, querying for pecks. returns peck time or "GoodNite" exception """

        if timeout is not None:
            start = time.time()

        while True:
            if not self._read_bool(channel):
                if self._state[channel]["pressed"]:
                    self._state[channel]["pressed"] = False
            elif not self._state[channel]["pressed"]:
                break

            if timeout is not None:
                if time.time() - start >= timeout: # Return GoodNite exception?
                    return None

        self._state[channel]["pressed"] = True
        return datetime.datetime.now()

    def _write_bool(self, channel, value):
        '''Write a value to the specified channel
        :param channel: the channel to write to
        :param value: the value to write
        :return: value written if succeeded
        '''

        if value:
            s = self.device.write(self._make_arg(channel, 1))
        else:
            s = self.device.write(self._make_arg(channel, 2))
        if s:
            return value
        else:
            raise InterfaceError('Could not write to serial device %s, channel %d' % (self.device, channel))

    @staticmethod
    def _make_arg(channel, value):

        return "".join([chr(channel), chr(value)])
