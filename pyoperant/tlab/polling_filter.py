import logging
import ipdb

class PollingFilter(logging.Filter):

    def filter(self, record):

        if record.msg.startswith("Polling: "):
            record.msg = record.msg.replace("Polling: ", "")
            return True

        return False
