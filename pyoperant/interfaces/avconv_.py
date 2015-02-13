import subprocess
import os
import signal
import threading
import copy
from pyoperant.interfaces import base_


class AVConvInterface(base_.BaseInterface):
    '''
    Interface for the library avconv for recording from webcams. This should function cross-platform but has only
    been tried on linux.
    TODO: Must look into errors that can be thrown and handle them. Specifically, what if the audio/video devices
    specified do not exist or do not open?
    '''

    def __init__(self, *args, **kwargs):

        super(AVConvInterface, self).__init__(*args, **kwargs)
        self.video = None
        self.audio = None

    def configure_video(self, device_name="/dev/video0", driver_name="video4linux2", **kwargs):
        '''
        Declare the parameters used to record video from a webcam.
        :param device_name: The name of the webcam as addressed by the computer
        :param driver_name: The video driver
        :param kwargs: Any additional parameters (e.g. framerate, frame_size, etc.). Values should all be strings
        :return:
        TODO: handle any errors. What is values aren't strings? What if device_name doesn't exist? etc.
        '''

        self.video = dict(name=device_name,
                          driver=driver_name)
        self.video.update(kwargs)

    def configure_audio(self, device_name="default", driver_name="alsa", **kwargs):
        '''
        Declare the parameters used to record audio from a webcam.
        :param device_name: The name of the microphone as addressed by the computer
        :param driver_name: The audio driver
        :param kwargs: Any additional parameters. Values should all be strings
        :return:
        '''

        self.audio = dict(name=device_name,
                          driver=driver_name)
        self.audio.update(kwargs)

    def snapshot(self, output_file, overwrite=False):

        if self.video:
            command = ["avconv"]

            video_params = copy.deepcopy(self.video)
            device = video_params.pop("name")
            driver = video_params.pop("driver")

            command += ["-f", driver]
            for key, value in video_params.iteritems():
                if key not in ["r", "framerate"]:
                    command += ["-%s" % key, value]
            command += ["-r", "1", "frames:v", "1"]
            command += ["-i", device]
            if overwrite:
                command.append("-y")
            command.append(output_file)

            p = subprocess.Popen(command,
                                 shell=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.communicate()

    def record(self, output_file, overwrite=False):

        class RecordingThread(threading.Thread):
            def __init__(self, command):
                self.command = command
                self.stdout = subprocess.PIPE
                self.stderr = subprocess.PIPE
                threading.Thread.__init__(self)

            def run(self):
                self.process = subprocess.Popen(self.command,
                                                shell=False,
                                                stdout=self.stdout,
                                                stderr=self.stderr)

                self.stdout, self.stderr = self.process.communicate()

        if os.path.exists(output_file) and (not overwrite):
            pass
            # do something here with the filename
            # output_file = ...

        command = ["avconv"]

        # Configure video parameters
        if self.video:
            video_params = copy.deepcopy(self.video)
            device = video_params.pop("name")
            driver = video_params.pop("driver")

            command += ["-f", driver]
            for key, value in video_params.iteritems():
                command += ["-%s" % key, value]
            command += ["-i", device]

        # Configure audio parameters
        if self.audio:
            audio_params = copy.deepcopy(self.audio)
            device = audio_params.pop("name")
            driver = audio_params.pop("driver")

            command += ["-f", driver]
            for key, value in audio_params.iteritems():
                command += ["-%s" % key, value]
            command += ["-i", device]

        # Add overwrite flag
        if overwrite:
            command.append("-y")
        command.append(output_file)

        # Create RecordingThread and run it
        self.recording_thread = RecordingThread(command)
        self.recording_thread.start()

    def stop(self):

        # Send SIGINT to the thread if it exists. This simulates Ctrl+C from command line, which is what avconv expects
        if self.recording_thread:
            try:
                self.recording_thread.process.send_signal(signal.SIGINT)
                # Close down recording_thread and set it to None
                self.recording_thread = None
            except OSError as e:
                print "Error stopping recording: %s" % e
