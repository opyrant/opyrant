import datetime as dt
import os

from pyoperant import hwio, components, panels, utils
from pyoperant.tlab import components_tlab, hwio_tlab
from pyoperant.interfaces import pyaudio_, arduino_  # , avconv_



class TLabPanel(panels.BasePanel):

    _default_sound_file = "/home/fet/test_song.wav"

    configuration = {"key_input": 4,
                     "key_light": 8,
                     "main_light": 9,
                     "feeder": 10,
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
                                                     "pullup": True}))


        self.outputs.append(hwio.BooleanOutput(name="Pecking key light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["key_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Main light",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["main_light"]}))
        self.outputs.append(hwio.BooleanOutput(name="Feeder",
                                               interface=self.interfaces['arduino'],
                                               params={"channel": self.configuration["feeder"]}))


        # Set up components
        self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        # self.camera = hwio.CameraInput(name="Webcam",
        #                                interface=self.interfaces['avconv'],
        #                                params={'video_params':{},
        #                                        'audio_params':{}}))

        self.peck_port = components.PeckPort(IR=self.inputs[0], LED=self.outputs[0])
        self.house_light = components.HouseLight(light=self.outputs[1])
        self.feeder = components_tlab.HopperNoIR(solenoid=self.outputs[2])

        # Translations
        self.response_port = self.peck_port

    def reward(self, value=12.0):

        self.feeder.up()
        peck_time = self.peck_port.poll(value)
        self.feeder.down()
        if peck_time is not None:
            return peck_time

        return True

    def punish(self):

        pass

    def reset(self):
        for output in self.outputs:
            output.write(False)
        self.house_light.on()
        self.feeder.down()

    def test(self):
        self.reset()

        print("Flashing pecking port")
        self.peck_port.flash(2.0, .1)
        print("Raising feeder")
        self.reward(5.0)

        print("Playing test sound")
        self.speaker.queue(os.path.expanduser('~/zbsong.wav'))
        self.speaker.play()

        print("Polling for input. Peck to proceed (10 second timeout)")
        self.peck_port.poll(10)
        self.speaker.stop()
        self.reset()
        return True

    def calibrate(self):

        self.peck_port.off()
        try:
            while True:
                is_pecked = self.peck_port.status()
                if is_pecked:
                    current_time = dt.datetime.now()
                    print("%s: Pecked!" % current_time.strftime("%H:%M:%S"))
                    self.peck_port.on()
                utils.wait(0.05)
                self.peck_port.off()
        except KeyboardInterrupt:
            print("Finished calibration")

    def check_poll_rate(self, iters=10, duration=10):
        import time

        num_polls = list()
        for ii in xrange(iters):
            print("Iteration %d: " % ii),
            count = 0
            current_time = time.time()
            while True:
                count += 1
                self.peck_port.status()
                if time.time() - current_time > duration:
                    break
            num_polls.append(count)
            print("%d" % count)

        return [float(pc) / duration for pc in num_polls]

    def test_audio(self, filename=""):

        if not filename:
            filename = self._default_sound_file

        print("Testing sound playback with %s" % filename)
        self.speaker.queue(filename)
        self.speaker.play()
        # close file after certain time

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

class Box5(TLabPanel):

    configuration = {"arduino": "/dev/ttyACM2",
                     "speaker": "speaker0"}

    def __init__(self, *args, **kwargs):
        super(Box5, self).__init__(self.configuration)


class Box6(TLabPanel):

    configuration = {"arduino": "/dev/ttyACM1",
                     "speaker": "default"}

    def __init__(self, *args, **kwargs):
        super(Box6, self).__init__(self.configuration)



PANELS = {"Thing1": Thing1,
          "Thing2": Thing2,
          "Box5": Box5,
          "Box6": Box6}
