import os
from pyoperant import hwio, components, panels, utils
from pyoperant.tlab import components_tlab, hwio_tlab
from pyoperant.interfaces import pyaudio_, arduino_  # , avconv_


class TLabPanel(panels.BasePanel):

    preconfigured = {1: {"arduino": "/dev/tty.usbmodemfa141",
                         "speaker": "Built-in Output",
                         "key_input": 4,
                         "key_light": 8,
                         "main_light": 9,
                         "hopper": 10,
                         },
                     2: {"arduino": "/dev/tty.usbserial",
                         "speaker": "sysdefault",
                         "key_input": 4,
                         "key_light": 8,
                         "main_light": 9,
                         "hopper": 10,
                         },
                     3: {"arduino": "/dev/ttyACM0",
                         "speaker": "speaker0",
                         "key_input": 4,
                         "key_light": 8,
                         "main_light": 9,
                         "hopper": 10,
                         },
                     }
    baud_rate = 19200

    def __init__(self, id_, *args, **kwargs):

        super(TLabPanel, self).__init__(self, *args, **kwargs)

        self.id = id_

        # Initialize interfaces
        self.interfaces['arduino'] = arduino_.ArduinoInterface(device_name=self.preconfigured[self.id]['arduino'],
                                                                baud_rate=self.baud_rate)
        self.interfaces['pyaudio'] = pyaudio_.PyAudioInterface(device_name=self.preconfigured[self.id]['speaker'])
        # self.interfaces['avconv'] = avconv_.AVConvInterface()

        # Create hardware inputs and outputs
        self.inputs.append(hwio.BooleanInput(name="Pecking key input",
                                             interface=self.interfaces['arduino'],
                                             params={"channel": self.preconfigured[self.id]["key_input"],
                                                     "pullup": True}))


        self.outputs.append(hwio.BooleanOutput(name="Pecking key light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.preconfigured[self.id]["key_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Main light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.preconfigured[self.id]["main_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Hopper",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.preconfigured[self.id]["hopper"]}))


        # Set up components
        self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        # self.camera = hwio.CameraInput(name="Webcam",
        #                                interface=self.interfaces['avconv'],
        #                                params={'video_params':{},
        #                                        'audio_params':{}}))

        self.peck_port = components.PeckPort(IR=self.inputs[0], LED=self.outputs[0])
        self.house_light = components.HouseLight(light=self.outputs[1])
        self.hopper = components_tlab.HopperNoIR(solenoid=self.outputs[2])

    def reward(self, duration=10.0):

        return self.hopper.reward(duration)

    def punish(self):

        pass

    def reset(self):
        for output in self.outputs:
            output.write(False)
        self.house_light.on()
        self.hopper.down()

    def test(self):
        self.reset()

        print("Flashing pecking port")
        self.peck_port.flash(2.0, .1)
        print("Raising hopper")
        self.reward(5.0)

        print("Playing test sound")
        self.speaker.queue(os.path.expanduser('~/zbsong.wav'))
        self.speaker.play()

        print("Polling for input. Peck to proceed (10 second timeout)")
        self.peck_port.poll(10)
        self.reset()
        return True

PANELS = {"Box1": lambda :TLabPanel(id=1),
          "Box2": lambda :TLabPanel(id=2)}
