import threading

class PollingThread(threading.Thread):

    def __init__(self, input):

        self.input = input
        super(PollingThread, self).__init__()

    def run(self, timeout=None):

        ts = self.input.poll(timeout=timeout)
        if ts is not None:
            print("Response at %s" % ts.ctime())

        return ts
