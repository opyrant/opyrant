import datetime as dt
import os
import logging
import argparse
from functools import wraps

from pyoperant import hwio, components, panels, utils, InterfaceError, events
from pyoperant.interfaces import nidaq_

logger = logging.getLogger(__name__)

class Panel131(panels.BasePanel):
    """ The chronic recordings box in room 131

    The speaker should probably be the address of the nidaq card

    Parameters
    ----------
    name: string
        Name of this box
    speaker: string
        Speaker device name for this box
    channel: string
        The channel name for the analog output
    input_channel: string
        The channel name for a boolean input (e.g. perch or peck-port)
        Default None means no input configured

    Attributes
    ----------

    Examples
    --------
    """

    _default_sound_file = "C:/DATA/stimuli/stim_test/1.wav"

    def __init__(self, speaker="Dev1", channel="ao0", input_channel=None, name=None, *args, **kwargs):
        super(Panel131, self).__init__(self, *args, **kwargs)
        self.name = name

        # Initialize interfaces
        speaker_out = nidaq_.NIDAQmxAudioInterface(device_name=speaker,
                                                   clock_channel="/Dev1/PFI0")

        # Create a digital to analog event handler
        analog_event_handler = events.EventDToAHandler(channel=speaker + "/" + "ao1",
                                                       scaling=3.3,
                                                       metadata_bytes=40)
        # Create an audio output
        audio_out = hwio.AudioOutput(interface=speaker_out,
                                     params={"channel": speaker + "/" + channel,
                                             "analog_event_handler": analog_event_handler})

        # Add boolean hwios to inputs and outputs
        self.inputs = []
        self.outputs = [audio_out]

        # Set up components
        self.speaker = components.Speaker(output=audio_out)

        if input_channel is not None:
            boolean_input = hwio.BooleanInput(name="Button",
                                              interface=speaker_out,
                                              params={"channel": speaker + "/" + input_channel,
                                                      "invert": True})
            self.inputs.append(boolean_input)
            self.button = components.Button(IR=boolean_input)

    def reset(self):

        pass

    def sleep(self):

        pass

    def ready(self):

        pass

    def idle(self):

        pass

    def poll_then_sound(self, timeout=None):

        if not hasattr(self, "button"):
            raise AttributeError("This panel does not have a button")

        self.speaker.queue(self._default_sound_file)
        self.button.poll(timeout=timeout)
        self.speaker.play()


class PanelWithInput(Panel131):

    def __init__(self, *args, **kwargs):

        super(PanelWithInput, self).__init__(name="Panel with input",
                                             input_channel="port0/line5")
