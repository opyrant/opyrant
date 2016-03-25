import threading
# import Queue
from multiprocessing import Process, Queue
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

class Events(object):

    def __init__(self):

        self.handlers = list()

    def add_handler(self, handler):

        if not hasattr(handler, "queue"):
            raise AttributeError("Event handler instance must contain a queue")

        self.handlers.append(handler)

    def write(self, event):

        event["time"] = time.time()
        for handler in self.handlers:
            # print("Adding to handler %s" % str(handler))
            handler.queue.put(event)


class EventHandler(object):

    STOP_FLAG = 0

    def __init__(self):

        # Initialize the queue
        # self.queue = Queue.Queue(maxsize=0)
        self.queue = Queue(maxsize=0)
        self.delay_queue = Queue(maxsize=0)

        # Initialize the thread
        # self.thread = threading.Thread(target=self.run, name=self.__class__.__name__)
        self.thread = Process(target=self.run, name=self.__class__.__name__)

        # Run the thread
        self.thread.start()

        self.delays = list()

    def run(self):

        while True:
            event = self.queue.get()
            if event is self.STOP_FLAG:
                logger.debug("Stopping thread %s" % self.thread.name)
                return

            self.write(event)

    def close(self):

        self.queue.put(self.STOP_FLAG)

    def __del__(self):

        self.close()


class EventInterfaceHandler(EventHandler):

    def __init__(self, interface, name_bytes=4, action_bytes=4,
                 metadata_bytes=16):

        super(EventInterfaceHandler, self).__init__()
        self.interface = interface
        self.name_bytes = name_bytes
        self.action_bytes = action_bytes
        self.metadata_bytes = metadata_bytes
        self.map_to_bit = dict()

    def write(self, event):

        if "time" in event:
            delay = time.time() - event["time"]
            print("Took %.4f seconds to write to interface handler" % delay)
            # self.delays.append(delay)
            self.delay_queue.put(delay)

        try:
            key = (event["name"], event["action"], event["metadata"])
            bits = self.map_to_bit[key]
        except KeyError:
            bits = self.to_bit_sequence(event)
        self.interface.write(bits)

    def to_bit_sequence(self, event):

        if event["metadata"] is None:
            nbytes = self.action_bytes + self.name_bytes
            metadata_array = []
        else:
            nbytes = self.metadata_bytes  + self.action_bytes + self.name_bytes
            try:
                metadata_array = np.fromstring(event["metadata"],
                                               dtype=np.uint16).astype(np.uint8)[:self.metadata_bytes]
            except TypeError:
                metadata_array = np.array(map(ord,
                                              event["metadata"].ljust(self.metadata_bytes)[:self.metadata_bytes]),
                                          dtype=np.uint8)

        int8_array = np.zeros(nbytes, dtype="uint8")
        int8_array[:self.name_bytes] = map(ord, event["name"].ljust(self.name_bytes)[:self.name_bytes])
        int8_array[self.name_bytes:self.name_bytes + self.action_bytes] = map(ord, event["action"].ljust(self.action_bytes)[:self.action_bytes])
        int8_array[self.name_bytes + self.action_bytes:] = metadata_array

        sequence = ([True] +
                    np.unpackbits(int8_array).astype(bool).tolist() +
                    [False])
        key = (event["name"], event["action"], event["metadata"])
        self.map_to_bit[key] = sequence

        return sequence


class EventLogHandler(EventHandler):

    def __init__(self, filename, format=None):

        super(EventLogHandler, self).__init__()
        self.filename = filename
        if format is None:
            self.format = "\t".join(["{time}",
                                     "{name}",
                                     "{action}",
                                     "{metadata}"])

    def write(self, event):

        if "time" in event:
            delay = time.time() - event["time"]
            print("Took %.4f seconds to write to log handler" % delay)
            # self.delays.append(delay)
            self.delay_queue.put(delay)

        if "time" not in event:
            event["time"] = time.time()

        with open(self.filename, "a") as fh:
            fh.write(self.format.format(**event) + "\n")

events = Events()

if __name__ == "__main__":

    ihandler = EventInterfaceHandler(None)
    events.add_handler(ihandler)
    for ii in range(100):
        events.write({})
        time.sleep(0.1)

    if ihandler.delay_queue.qsize() > 0:
        for ii in range(ihandler.delay_queue.qsize()):
            ihandler.delays.append(ihandler.delay_queue.get())

    print("Mean delay was %.4e seconds" % (sum(ihandler.delays) / 100))
    print("Max delay was %.4e seconds" % max(ihandler.delays))
