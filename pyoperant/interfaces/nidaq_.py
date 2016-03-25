import logging
import numpy as np
import nidaqmx
import wave
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError

logger = logging.getLogger(__name__)


def list_devices():

    return nidaqmx.System().devices


class NIDAQmxError(Exception):
    pass


class NIDAQmxInterface(base_.BaseInterface):
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
                 *args, **kwargs):
        """
        Creates an interface for boolean inputs and outputs to a NIDAQ card
        :param device_name: the name of the device on your system
        :param samplerate: the samplerate for all inputs and outputs.
        If an external clock is specified, then this should be the maximum
        allowed samplerate.
        :param clock_channel: the channel name for an external clock signal
        """
        super(NIDAQmxInterface, self).__init__(*args, **kwargs)
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

    def _config_read(self, channels, **kwargs):
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
        task.set_buffer_size(0)
        self.tasks[channels] = task

    def _config_write(self, channels, **kwargs):
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
        task.set_buffer_size(0)
        self.tasks[channels] = task

    def _read_bool(self, channels, **kwargs):

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))
        task = self.tasks[channels]
        if isinstance(task, nidaqmx.DigitalOutputTask):
            raise WriteCannotBeReadError("Cannot read from output task")

        task.read()

    def _write_bool(self, channels, value, **kwargs):

        if channels not in self.tasks:
            raise NIDAQmxError("Channel(s) %s not yet configured" % str(channels))
        task = self.tasks[channels]
        task.write(value, auto_start=True)

    def _config_read_analog(self, channels, min_val=-10.0, max_val=10.0,
                            **kwargs):
        """
        Configure a channel or group of channels as a boolean input
        :param channels: a channel or group of channels that will all be read
        from at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring analog input on channel(s) %s" % str(channels))
        task = nidaqmx.AnalogInputTask()
        task.create_voltage_channel(channels, min_val=min_val, max_val=max_val)
        task.configure_timing_sample_clock(source=selsf.clock_channel,
                                           rate=self.samplerate,
                                           sample_mode="finite")
        self.tasks[channels] = task

    def _config_write_analog(self, channels, min_val=-10.0, max_val=10.0,
                             **kwargs):
        """
        Configure a channel or group of channels as a boolean output
        :param channels: a channel or group of channels that will all be written
        to at the same time
        """

        # TODO: test multiple channels. What format should channels be in?
        logger.debug("Configuring analog output on channel(s) %s" % str(channels))
        task = nidaqmx.AnalogOutputTask()
        task.create_voltage_channel(channels, min_val=min_val, max_val=max_val)
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate,
                                           sample_mode="finite")
        self.tasks[channels] = task

    def _read_analog(self, channels, nsamples, **kwargs):
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
        if isinstance(task, nidaqmx.AnalogOutputTask):
            raise WriteCannotBeReadError("Cannot read from output task")

        task.set_buffer_size(nsamples)

        return task.read(nsamples)

    def _write_analog(self, channels, values, is_blocking=False, **kwargs):
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
        task.stop()
        task.set_buffer_size(len(values))
        task.write(values, auto_start=False)
        task.start()
        if is_blocking:
            task.wait_until_done()
            task.stop()


class NIDAQmxAudioInterface(NIDAQmxInterface, base_.AudioInterface):

    def __init__(self, device_name="Dev1", samplerate=30000.0, clock_channel=None,
                 *args, **kwargs):

        super(NIDAQmxAudioInterface, self).__init__(device_name=device_name,
                                                    samplerate=samplerate,
                                                    clock_channel=clock_channel,
                                                    *args, **kwargs)
        self.stream = None
        self.wf = None
        self.wav_data = None

    def _config_write_analog(self, channel, min_val=-10.0, max_val=10.0,
                             **kwargs):

        super(NIDAQmxAudioInterface, self)._config_write_analog(channel,
                                                                min_val=min_val,
                                                                max_val=max_val,
                                                                **kwargs)
        self.stream = self.tasks.values()[0]

    def _queue_wav(self, wav_file, start=False, **kwargs):

        if self.wf is not None:
            self._stop_wav()

        logger.debug("Queueing wavfile %s" % wav_file)
        self.wf = wave.open(wav_file)
        self.validate()
        sampwidth = self.wf.getsampwidth()
        if sampwidth == 2:
            max_val = 32768.0
            dtype = np.int16
        elif sampwidth == 4:
            max_val = float(2 ** 32)
            dtype = np.int32
        data = np.fromstring(self.wf.readframes(-1), dtype=dtype)
        self.wav_data = (data / max_val).astype(np.float64)
        self._get_stream(start=start, **kwargs)

    def _get_stream(self, start=False, **kwargs):
        """
        """

        self.stream.configure_timing_sample_clock(source=self.clock_channel,
                                                  rate=self.samplerate,
                                                  sample_mode="finite",
                                                  samples_per_channel=len(self.wav_data))
        self.stream.write(self.wav_data, auto_start=False)
        if start:
            self._play_wav(**kwargs)

    def _play_wav(self, is_blocking=False):
        logger.debug("Playing wavfile")
        # self.event.write()
        self.stream.start()
        if is_blocking:
            self.wait_until_done()

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

        self.wav_data = None
