__author__ = 'tlee'
from pyoperant import hwio, components, panels, utils
from pyoperant.interfaces import pyaudio_

class TLabPanel(panels.BasePanel):

    def __init__(self, *args, **kwargs):
        super(TLabPanel, self).__init__(self, *args, **kwargs)

        # self.interfaces['pyaudio'] = pyaudio_.PyAudioInterface(device_name='') #callback should be related to pecking
        # self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        #
        # # assemble inputs into components
        # self.left = components.PeckPort(IR=self.inputs[0],LED=self.outputs[0],name='l')
        # self.center = components.PeckPort(IR=self.inputs[1],LED=self.outputs[1],name='c')
        # self.right = components.PeckPort(IR=self.inputs[2],LED=self.outputs[2],name='r')
        # self.house_light = components.HouseLight(light=self.outputs[3])
        # self.hopper = components.Hopper(IR=self.inputs[3],solenoid=self.outputs[4])
        #
        # # define reward & punishment methods
        # self.reward = self.hopper.reward
