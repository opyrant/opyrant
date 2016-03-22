import logging
import numpy as np
import nidaqmx
from scipy.io import wavfile # TODO: switch to built-in wave
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError

logger = logging.getLogger(__name__)


def list_devices():

    return nidaqmx.System().devices


class NIDAQmxError(Exception):
    pass

class NIDAQmxDigitalInterface(base_.BaseInterface):
    """
    Creates an interface for boolean inputs and outputs to a NIDAQ card using
    the pylibnidaqmx library: https://github.com/imrehg/pylibnidaqmx

    Examples:
    dev = NIDAQmxDigitalInterface("Dev1") # open the device at "Dev1"
    # or with an external clock
    dev = NIDAQmxDigitalInterface("Dev1", clock_channel="/Dev1/PFI0")

    # Configure a boolean output on port 0, line 0
    dev._config_write("Dev1/port0/line0")
    # Set the output to True
    dev._write_bool("Dev1/port0/line0", True)

    # Configure a boolean input on port 0, line 1
    dev._config_read("Dev1/port0/line1")
    # Read from that input
    dev._read_bool("Dev1/port0/line1")
    """

    def __init__(self, device_name="Dev1", samplerate=30000, clock_channel=None,
                 *args, **kwargs):
        """
        Creates an interface for boolean inputs and outputs to a NIDAQ card
        :param device_name: the name of the device on your system
        :param samplerate: the samplerate for all inputs and outputs.
        If an external clock is specified, then this should be the maximum
        allowed samplerate.
        :param clock_channel: the channel name for an external clock signal
        """
        super(NIDAQmxDigitalInterface, self).__init__(*args, **kwargs)
        self.device_name = device_name
        self.samplerate = samplerate
        self.clock_channel = clock_channel

        self.tasks = dict()
        self.open()

    def open(self):
        """ Opens the nidaqmx device """

        logger.debug("Opening nidaqmx device named %s" % self.device_name)
        self.device = nidaqmx.Device(self.device_name)

    def close(self):
        """ Closes the nidaqmx device and deletes all of the tasks """

        logger.debug("Closing nidaqmx device named %s" % self.device_name)
        for task in self.tasks.values():
            logger.debug("Deleting task named %s" % str(task.name))
            task.stop()
            task.clear()
            del task
        self.tasks = dict()

    def _config_read(self, channels):
        """
        Configure a channel or group of channels as a boolean input
        :param channels: a channel or group of channels that will all be read
        from at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring digital input on channel(s) %s" % str(channels))
        task = nidaqmx.DigitalInputTask()
        task.create_channel(channels)
        task.configure_timing_sample_clock(source=selsf.clock_channel,
                                           rate=self.samplerate)
        # TODO: Here we don't set buffer size to 0. Why not?
        self.tasks[channels] = task

    def _config_write(self, channels):
        """
        Configure a channel or group of channels as a boolean output
        :param channels: a channel or group of channels that will all be written
        to at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring digital output on channel(s) %s" % str(channels))
        task = nidaqmx.DigitalOutputTask()
        task.create_channel(channels)
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        # TODO: This locks the buffer to the hardware clock. Do we want this in case of sending multiple bits?
        task.set_buffer_size(0)
        self.tasks[channels] = task

    def _read_bool(self, channels):

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))

        task = self.tasks[channels]
        task.read()

    def _write_bool(self, channels, value):

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))
        task = self.tasks[channels]
        task.write(value, auto_start=True)


class NIDAQmxAnalogInterface(base_.BaseInterface):
    """
    Creates an interface for analog inputs and outputs to a NIDAQ card using
    the pylibnidaqmx library: https://github.com/imrehg/pylibnidaqmx

    Examples:
    dev = NIDAQmxAnalogInterface("Dev1") # open the device at "Dev1"
    # or with an external clock
    dev = NIDAQmxAnalogInterface("Dev1", clock_channel="/Dev1/PFI0")

    # Configure an analog output on channel ao0
    dev._config_write("Dev1/ao0")
    # Set the output to True
    dev._write("Dev1/ao0", True)

    # Configure a boolean input on channel ai0
    dev._config_read("Dev1/ai0")
    # Read from that input
    dev._read("Dev1/ai0")
    """

    def __init__(self, device_name="Dev1", samplerate=30000, clock_channel=None,
                 chunk_size=256, *args, **kwargs):
        """
        Creates an interface for boolean inputs and outputs to a NIDAQ card
        :param device_name: the name of the device on your system
        :param samplerate: the samplerate for all inputs and outputs.
        If an external clock is specified, then this should be the maximum
        allowed samplerate.
        :param clock_channel: the channel name for an external clock signal
        """
        super(NIDAQmxAnalogInterface, self).__init__(*args, **kwargs)
        self.device_name = device_name
        self.samplerate = samplerate
        self.clock_channel = clock_channel

        self.tasks = dict()
        self.open()

    def open(self):
        """ Opens the nidaqmx device """

        logger.debug("Opening nidaqmx device named %s" % self.device_name)
        self.device = nidaqmx.Device(self.device_name)

    def close(self):
        """ Closes the nidaqmx device and deletes all of the tasks """

        logger.debug("Closing nidaqmx device named %s" % self.device_name)
        for task in self.tasks.values():
            logger.debug("Deleting task named %s" % str(task.name))
            task.stop()
            task.clear()
            del task
        self.tasks = dict()

    def _config_read(self, channels):
        """
        Configure a channel or group of channels as a boolean input
        :param channels: a channel or group of channels that will all be read
        from at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring analog input on channel(s) %s" % str(channels))
        task = nidaqmx.AnalogInputTask()
        task.create_channel(channels)
        task.configure_timing_sample_clock(source=selsf.clock_channel,
                                           rate=self.samplerate)
        self.tasks[channels] = task

    def _config_write(self, channels):
        """
        Configure a channel or group of channels as a boolean output
        :param channels: a channel or group of channels that will all be written
        to at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring analog output on channel(s) %s" % str(channels))
        task = nidaqmx.AnalogOutputTask()
        task.create_channel(channels)
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        self.tasks[channels] = task

    def _read(self, channels, nsamples, **kwargs):
        """
        Read from a channel or group of channels for the specified number of
        samples.
        :param channels: a channel or group of channels that will be read at
        the same time
        :param nsamples: the number of samples to read

        :returns a numpy array of the data that was read
        """

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))

        task = self.tasks[channels]
        task.read()

    def _write(self, channels, values):
        """
        Write a numpy array of float64 values to the buffer on a channel or
        group of channels
        :param channels: a channel or group of channels that will be written to
        at the same time
        :param values: must be a numpy array of float64 values
        """

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))

        task = self.tasks[channel]
        task.write(value, auto_start=True)


class NIDAQmxAudioInterface(base_.AudioInterface):

    def __init__(self, device_name="Dev1", samplerate=30000.0, clock_channel=None,
                 *args, **kwargs):

        super(NIDAQmxAudioInterface, self).__init__(*args, **kwargs)
        self.device_name = device_name
        self.samplerate = samplerate
        self.clock_channel = clock_channel
        self.stream = None

        self.open()

    def open(self):
        """ Opens the nidaqmx device """

        logger.debug("Opening nidaqmx device named %s" % self.device_name)
        self.device = nidaqmx.Device(self.device_name)

    def close(self):
        """ Closes the nidaqmx device and deletes the audio task """

        logger.debug("Closing nidaqmx device named %s" % self.device_name)
        logger.debug("Deleting task named %s" % str(self.stream.name))
        self.stream.stop()
        self.stream.clear()
        del self.stream
        self.stream = None

    def _config_write(self, channel, name=None,
                      min_val=-10.0, max_val=10.0, **kwargs):

        logger.debug("Configuring audio output on channel %s" % str(channel))
        task = nidaqmx.AnalogOutputTask()
        # TODO: what should we do about max_val and min_val?
        task.create_voltage_channel(channel, min_val=min_val, max_val=max_val)
        # TODO: It seems the sample_clock has to be set to the number of samples of the wavefile
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        self.stream = task

    def _queue_wav(self, wav_file, start=False):
        logger.debug("Queueing wavfile %s" % wav_file)
        self.data = self.load_wav(wav_file)
        self.validate()
        self._get_stream(start=start)

    def _get_stream(self, start=False):
        """
        """

        self.stream.configure_timing_sample_clock(source=self.clock_channel,
                                                  rate=self.samplerate,
                                                  sample_mode="finite",
                                                  samples_per_channel=len(self.wf))
        self.stream.write(self.wf, auto_start=start)

    def _play_wav(self):
        logger.debug("Playing wavfile")
        # self.event.write()
        self.stream.start()

    def _stop_wav(self):
        try:
            logger.debug("Attempting to close stream")
            self.stream.stop()
            logger.debug("Stream closed")
        except AttributeError:
            self.stream = None
        try:
            self.wf.close()
        except AttributeError:
            self.wf = None
