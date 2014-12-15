from pyoperant import hwio, components, panels, utils
from pyoperant.tlab import components_tlab, hwio_tlab
from pyoperant.interfaces import pyaudio_, arduino_


_BOX_MAP = {1: ("/dev/tty.usbmodemfd131", [4], [8, 9, 10], "Built-in Output"),
            2: ("/dev/tty.usbserial", [4], [8, 9, 10], "sysdefault"),
            }
class TLabPanel(panels.BasePanel):

    baud_rate = 19200

    def __init__(self, id=None, *args, **kwargs):
        super(TLabPanel, self).__init__(self, *args, **kwargs)

        self.id = id
        self.interfaces['pyserial'] = arduino_.ArduinoInterface(device_name=_BOX_MAP[self.id][0], baud_rate=self.baud_rate)
        self.interfaces['pyaudio'] = pyaudio_.PyAudioInterface(device_name=_BOX_MAP[self.id][3]) #callback should be related to pecking
        self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        #
        # # assemble inputs into components
        for ii in _BOX_MAP[self.id][1]:
            self.inputs.append(hwio_tlab.ConfigurableBooleanInput(interface=self.interfaces["pyserial"],
                                                                  params={"channel": ii},
                                                                  config_params={"pullup": False}))
        for ii in _BOX_MAP[self.id][2]:
            self.outputs.append(hwio.BooleanOutput(interface=self.interfaces["pyserial"],
                                                   params={"channel": ii}))

        self.response_port = components.PeckPort(IR=self.inputs[0],LED=self.outputs[0],name='c')
        self.house_light = components.HouseLight(light=self.outputs[1])
        self.hopper = components_tlab.HopperNoIR(solenoid=self.outputs[2])

        # define reward & punishment methods
        self.reward = self.hopper.reward
        self.punish = None

    def reset(self):
        for output in self.outputs:
            output.write(False)
        self.house_light.on()
        self.hopper.down()

    def test(self):
        self.reset()
        dur = 2.0
        for output in self.outputs:
            output.write(True)
            utils.wait(dur)
            output.write(False)
        self.reset()
        self.reward(value=dur)
        self.speaker.queue('/Users/tylerlee/code/neosound/data/zbsong.wav')
        self.speaker.play()
        return True



class Box1(TLabPanel):

    def __init__(self, *args, **kwargs):

        super(Box1, self).__init__(id=1, *args, **kwargs)

class Box2(TLabPanel):

    def __init__(self, *args, **kwargs):

        super(Box2, self).__init__(id=2, *args, **kwargs)

PANELS = {"Box1": Box1,
          "Box2": Box2}