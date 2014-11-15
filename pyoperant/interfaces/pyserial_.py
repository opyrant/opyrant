import serial
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError


class PySerialInterface(base_.BaseInterface):
    """Creates a pyserial interface to communicate with a serial accessible device such as an arduino.
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
    """
    def __init__(self,device_name,*args,baud_rate=9600,**kwargs):
        super(PySerialInterface, self).__init__(*args,**kwargs)
        self.device_name = device_name
        self.read_params = ('channel',
                            )
        self.baud_rate = baud_rate
        self.open()

    def open(self):
        '''Open a serial connection for the device
        May want to add some checks to make sure it opened and read some response from the device when it does.
        :return: None
        '''

        self.device = serial.Serial(self.device_name, self.baud_rate)
        if self.device is None:
            raise InterfaceError('could not open serial device %s' % self.device_name)

    def close(self):
        '''Close a serial connection for the device
        :return: None
        '''

        self.device.close()

    def _config_read(self,channel):
        ''' Configure the channel to act as an input
        :param channel: the channel number to configure
        :return: None
        '''

        self.device.write(self._make_arg(channel, 4))

    def _config_write(self,channel):
        ''' Configure the channel to act as an output
        :param channel: the channel number to configure
        :return: None
        '''

        self.device.write(self._make_arg(channel, 3))

    def _read_bool(self,channel):
        ''' Read a value from the specified channel
        :param channel: the channel from which to read
        :return: value
        '''

        self.device.write(self._make_arg(channel, 0))
        v = ord(self.device.read()) # Read hangs until the values are read. Not sure how to work with this
        if v:
            return v
        else:
            raise InterfaceError('could not read from serial device "%s", channel %d' % (self.device,channel))

    def _poll(self,channel):
        """ runs a loop, querying for pecks. returns peck time or "GoodNite" exception """
        date_fmt = '%Y-%m-%d %H:%M:%S.%f'
        timestamp = subprocess.check_output(['comedi_poll', self.device_name, '-s', str(subdevice), '-c', str(channel)])
        return datetime.datetime.strptime(timestamp.strip(),date_fmt)

    def _write_bool(self,channel,value):
        '''Write a value to the specified channel
        :param channel: the channel to write to
        :param value: the value to write
        :return: True if write succeeded
        '''

        if value:
            s = self.device.write(self._make_arg(channel, 1))
        else:
            s = self.device.write(self._make_arg(channel, 2))
        if s:
            return True
        else:
            raise InterfaceError('could not write to serial device "%s", channel %d' % (self.device,channel))

    def _make_arg(self, channel, value):

        return [chr(channel), chr(value)]

