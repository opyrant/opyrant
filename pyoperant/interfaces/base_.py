import time
import datetime
import logging
from pyoperant import InterfaceError

logger = logging.getLogger(__name__)

class BaseInterface(object):
    """
    Implements generic interface methods.
    Implemented methods:
    - _poll
    """
    def __init__(self, *args, **kwargs):

        super(BaseInterface, self).__init__()
        self.device_name = None

    def open(self):
        pass

    def close(self):
        pass

    def _poll(self, timeout=None, wait=None, *args, **kwargs):
        """
        Runs a loop, querying for the boolean input to return True.
        :param timeout: the time, in seconds, until polling times out.
        Defaults to no timeout.
        :param wait: the time, in seconds, to wait between subsequent reads
        (default no wait).

        :return: timestamp of True read
        """

        if timeout is not None:
            start = time.time()

        logger.debug("Begin polling from device %s" % self.device_name)
        while True:
            if self._read_bool(**params):
                break

            if timeout is not None:
                if time.time() - start >= timeout:
                    logger.debug("Polling timed out. Returning")

            if wait is not None:
                utils.wait(wait)

        logger.debug("Input detected. Returning")
        return datetime.datetime.now()

    def __del__(self):
        self.close()


class AudioInterface(BaseInterface):
    """
    Generic audio interface that implements wavefile handling
    Implemented methods:
    - validate
    -
    """

    def __init__(self, *args, **kwargs):

        super(AudioInterface, self).__init__()
        self.wf = None

    def _config_write(self, *args, **kwargs):

        pass

    def validate(self):
        """
        Verifies simply that the wav file has been opened. Could do other
        checks in the future.
        """

        if self.wf is None:
            raise InterfaceError("wavefile is not open, but it should be")

    def load_wav(self, filename):

        wf = wave.open(filename, "r")
