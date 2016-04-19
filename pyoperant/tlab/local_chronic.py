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

    Attributes
    ----------

    Examples
    --------
    """

    _default_sound_file = "/home/fet/test_song.wav"

    def __init__(self, speaker="Dev1", channel="ao0", name=None, *args, **kwargs):
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
        self.outputs = []

        # Set up components
        self.speaker = components.Speaker(output=audio_out)

    def reset(self):  

        pass

    def sleep(self):

        pass

    def ready(self):

        pass

    def idle(self):

        pass


class Thing13_131(Panel131):

    _default_sound_file = "/home/tlee/code/neosound/data/zbsong.wav"

    def __init__(self, *args, **kwargs):

        super(Thing13_131, self).__init__(name="Tyler's Laptop",
                                          speaker="pulse")
