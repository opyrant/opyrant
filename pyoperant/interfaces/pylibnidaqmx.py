import logging
import numpy as np
import nidaqmx
from scipy.io import wavfile # TODO: switch to built-in wave
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError

logger = logging.getLogger(__name__)

class NIDAQmxInterface(base_.BaseInterface):

    # TODO: What to do if multiple audio outputs are desired?

    def __init__(self, device_name="Dev1", samplerate=30000, clock_channel=None,
                 *args, **kwargs):
        # Initialize the device
        super(NIDAQmxInterface, self).__init__(*args, **kwargs)
        self.device_name = device_name
        self.samplerate = samplerate
        self.clock_channel = clock_channel
        self.device_index = None
        self.tasks = dict()
        self.audio = None
        self.stream = None
        self.wf = None
        self.callback = None
        self.open()

    def open(self):

        logger.debug("Opening nidaqmx device named %s" % self.device_name)
        self.device = nidaqmx.Device(self.device_name)

    def close(self):

        logger.debug("Closing nidaqmx device named %s" % self.device_name)
        for task in self.tasks.values():
            logger.debug("Deleting task named %s" % str(task.name))
            task.stop()
            task.clear()
            del task

    def _config_read(self, channel, name=None):

        logger.debug("Configuring digital input on channel %s" % str(channel))
        task = nidaqmx.DigitalInputTask()
        task.create_channel(channel)
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        self.tasks[channel] = task

    def _config_write(self, channel, name=None):

        logger.debug("Configuring digital output on channel %s" % str(channel))
        task = nidaqmx.DigitalOutputTask()
        task.create_channel(channel)
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        task.set_buffer_size(0)
        self.tasks[channel] = task

    def _config_audio(self, channel, name=None,
                      min_val=-10.0, max_val=10.0):

        logger.debug("Configuring analog output on channel %s" % str(channel))
        task = nidaqmx.AnalogOutputTask()
        # TODO: what should we do about max_val and min_val?
        task.create_voltage_channel(channel, min_val=min_val, max_val=max_val)
        # TODO: It seems the sample_clock has to be set to the number of samples of the wavefile
        task.configure_timing_sample_clock(source=self.clock_channel,
                                           rate=self.samplerate)
        self.tasks[channel] = task
        self.audio = task

    def _read_bool(self, channel):

        task = self.tasks[channel]
        task.read()

    def _poll(self):

        pass

    def _write_bool(self, channel, value):

        task = self.tasks[channel]
        task.write(value, auto_start=True)

    def validate(self):
        if self.wf is not None:
            return True
        else:
            raise InterfaceError('there is something wrong with this wav file')

    def _get_stream(self, start=False):
        """
        """

        self.audio.configure_timing_sample_clock(source=self.clock_channel,
                                                 rate=self.samplerate,
                                                 sample_mode="finite",
                                                 samples_per_channel=len(self.wf))
        self.audio.write(self.wf, auto_start=start)

    def _queue_wav(self, wav_file, start=False):
        logger.debug("Queueing wavfile %s" % wav_file)
        # Check if audio is still playing?
        fs, self.wf = wavfile.read(wav_file)
        self.wf = self.wf.astype("float64") / self.wf.max() # TODO: broken
        if fs != self.samplerate:
            logger.warning("Samplerate of %s is %1.1f" % (wav_file, fs))
        self.validate()
        self._get_stream(start=start)

    def _play_wav(self):
        logger.debug("Playing wavfile")
        self.audio.start()

    def _stop_wav(self):
        try:
            logger.debug("Attempting to close stream")
            # self.stream.stop_stream()
            # logger.debug("Stream stopped")
            # while self.stream.is_active():
            #     logger.debug("Stream is still active!")
            #     pass
            self.audio.stop()
            logger.debug("Stream closed")
        except AttributeError:
            self.audio = None
        try:
            self.wf.close()
        except AttributeError:
            self.wf = None
