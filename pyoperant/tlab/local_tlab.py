import datetime as dt
from pyoperant import hwio, components, panels, utils
from pyoperant.tlab import components_tlab, hwio_tlab
from pyoperant.interfaces import pyaudio_, arduino_  # , avconv_



class TLabPanel(panels.BasePanel):

    configuration = {"key_input": 4,
                     "key_light": 8,
                     "main_light": 9,
                     "hopper": 10,
                     }
    baud_rate = 19200

    def __init__(self, configuration, *args, **kwargs):

        super(TLabPanel, self).__init__(self, *args, **kwargs)

        self.configuration = TLabPanel.configuration.copy()
        self.configuration.update(configuration)

        # Initialize interfaces
        self.interfaces['arduino'] = arduino_.ArduinoInterface(device_name=self.configuration['arduino'],
                                                                baud_rate=self.baud_rate)
        self.interfaces['pyaudio'] = pyaudio_.PyAudioInterface(device_name=self.configuration['speaker'])
        # self.interfaces['avconv'] = avconv_.AVConvInterface()

        # Create hardware inputs and outputs
        self.inputs.append(hwio.BooleanInput(name="Pecking key input",
                                             interface=self.interfaces['arduino'],
                                             params={"channel": self.configuration["key_input"],
                                                     "pullup": True,
                                                     "wait": 0.1}))


        self.outputs.append(hwio.BooleanOutput(name="Pecking key light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["key_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Main light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["main_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Hopper",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["hopper"]}))


        # Set up components
        self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        # self.camera = hwio.CameraInput(name="Webcam",
        #                                interface=self.interfaces['avconv'],
        #                                params={'video_params':{},
        #                                        'audio_params':{}}))

        self.peck_port = components.PeckPort(IR=self.inputs[0], LED=self.outputs[0])
        self.house_light = components.HouseLight(light=self.outputs[1])
        self.hopper = components_tlab.HopperNoIR(solenoid=self.outputs[2])

        # Translations
        self.response_port = self.peck_port

    def reward(self, value=10.0):

        self.hopper.up()
        peck_time = self.peck_port.poll(value)
        self.hopper.down()
        if peck_time is not None:
            return peck_time

        return True

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

    def calibrate(self):

        self.peck_port.off()
        while True:
            is_pecked = self.peck_port.status()
            if is_pecked:
                current_time = dt.datetime.now()
                print("%s: Pecked!" % current_time.strftime("%H:%M:%S"))
                self.peck_port.on()
            utils.wait(0.05)
            self.peck_port.off()



    def ready(self):

        self.peck_port.on()

    def idle(self):

        self.peck_port.off()


class Thing1(TLabPanel):

    configuration = {"arduino": "/dev/ttyACM0",
                     "speaker": "speaker0"}

    def __init__(self, *args, **kwargs):

        super(Thing1, self).__init__(self.configuration)


class Thing2(TLabPanel):

    configuration = {"arduino": "/dev/ttyUSB0",
                     "speaker": "speaker1"}

    def __init__(self, *args, **kwargs):

        super(Thing2, self).__init__(self.configuration)





PANELS = {"Thing1": Thing1,
          "Thing2": Thing2}
