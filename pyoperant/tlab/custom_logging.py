import logging
import time

# TODO: Document. How do these filters work? What do they do?

class PollingFilter(logging.Filter):

    def __init__(self, min_interval=.1, *args, **kwargs):

        super(PollingFilter, self).__init__(*args, **kwargs)
        self._min_interval = min_interval
        self._last_msg = None

    def filter(self, record):

        if record.msg.startswith("Polling: "):
            msg_time = time.time()
            if self._last_msg is not None:
                if msg_time - self._last_msg <= self._min_interval:
                    return False
            self._last_msg = msg_time
            record.msg = record.msg.replace("Polling: ", "")
            return True

        return False


class AudioPlaybackFilter(logging.Filter):

    def __init__(self, *args, **kwargs):

        super(AudioPlaybackFilter, self).__init__(*args, **kwargs)

    def filter(self, record):

        if record.msg.startswith("Playing"):
            record.msg = "Playing"
            return True
        elif record.msg.startswith("Stream closed"):
            record.msg = "Stopped"
            return True

        return False
