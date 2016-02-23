import logging
import numpy as np
from pyoperant import EndSession, EndExperiment, ComponentError, InterfaceError, utils

logger = logging.getLogger(__name__)
def log_error_callback(err):

    if isinstance(err, (InterfaceError, ComponentError)):
        logger.critical(repr(err))

def run_state_machine(experiment, start_in='pre', error_state=None, error_callback=None, **states):
    """runs a state machine defined by the keyword arguments

    >>> def run_start():
    >>>    print "in 'run_start'"
    >>>    return 'next'
    >>> def run_next():
    >>>    print "in 'run_next'"
    >>>    return None
    >>> run_state_machine(start_in='start',
    >>>                   start=run_start,
    >>>                   next=run_next)
    in 'run_start'
    in 'run_next'
    None
    """
    if error_callback is None:
        error_callback = log_error_callback

    # make sure the start state has a function to run
    assert (start_in in states.keys())
    # make sure all of the arguments passed in are callable
    for state in states.values():
        assert hasattr(state, "run")

    state_name = start_in
    while state_name is not None:
        try:
            with states[state_name](experiment) as state:
                state_name = state.run()
        except EndExperiment:
            state_name = None
        except Exception as e:
            if error_callback:
                error_callback(e)
                raise
            else:
                raise
            state_name = error_state


class State(object):

    def __init__(self, experiment):

        self.experiment = experiment

    def __enter__(self):

        logger.info("Entering %s state" % self.__class__.__name__)

        return self

    def __exit__(self, type_, value, traceback):

        logger.info("Exiting %s state" % self.__class__.__name__)
        if isinstance(value, Exception):
            log_error_callback(value)

        return False

    def run(self):

        pass


class TestState(State):

    def __init__(self, experiment=None):

        self.name = "some name"
        pass

    def __enter__(self):

        print "Entering: name = %s" % self.name
        return self

    def __exit__(self, type_, value, traceback):

        print "Exiting"
        print "type is %s" % str(type_)
        print "value is %s" % repr(value)
        print "traceback is %s" % str(traceback)

        if type_ in [KeyboardInterrupt]:
            print "Caught %s" % value
            return True

        return False

    def run(self):

        import time
        print "Running test state"
        print "name is %s" % self.name
        while True:
            time.sleep(10)

class Session(State):

    def __enter__(self):

        self.experiment.session_pre()

        return self

    def run(self):

        try:
            self.experiment.session_main()
        except EndSession:
            logger.info("Session has ended")
        except KeyboardInterrupt:
            logger.info("Finishing experiment")
            self.experiment.end()

        return "idle"

    def __exit__(self, type_, value, traceback):

        self.experiment.session_post()

        return super(Session, self).__exit__(type_, value, traceback)


class Idle(State):

    def run(self):

        try:
            if self.experiment.check_light_schedule() == False:
                return "sleep"
            elif self.experiment.check_session_schedule():
                return "session"
            else:
                if hasattr(self.experiment.panel, "idle"):
                    self.experiment.panel.idle()
                else:
                    self.experiment.panel.reset()
                logger.debug("idling...")
                utils.wait(self.experiment.parameters["idle_poll_interval"])
                return "idle"
        except KeyboardInterrupt:
            logger.info("Exiting experiment")
            raise


class Sleep(State):

    def run(self):

        logger.debug("sleeping")
        self.experiment.panel.sleep()
        utils.wait(self.experiment.parameters["idle_poll_interval"])
        if self.experiment.check_light_schedule() == False:
            return "sleep"
        else:
            return "idle"

    def __exit__(self, type_, value, traceback):

        self.experiment.panel.wake()
        return super(Sleep, self).__exit__(type_, value, traceback)


class BaseScheduler(object):

    def __init__(self):

        pass

    def start(self):

        pass

    def stop(self):

        pass

    def trigger_start(self):

        return False

    def trigger_stop(self):

        return False


class ResponseScheduler(BaseScheduler):

    def __init__(self, num_responses=np.inf, num_rewarded=np.inf):

        self.num_responses = num_responses
        self.num_rewarded = num_rewarded

        self.responses = None
        self.rewarded = None

    def start(self):

        self.responses = 0
        self.rewarded = 0

    def trigger_stop(self):

        if (self.responses >= self.num_responses) or (self.rewarded >= self.num_rewarded):

            return True

        else:
            self.responses += 1
            self.rewarded += 1

            return False


class TimeScheduler(BaseScheduler):

    def __init__(self, duration=np.inf, interval=np.inf):

        self.duration = duration
        self.interval = interval

        self.start_time = None
        self.stop_time = None

    def start(self):

        self.start_time = dt.datetime.now()

    def trigger_start(self):

        current_time = dt.datetime.now()
        if current_time - self.stop_time >= interval:
            return True
        else:
            return False

    def stop(self):

        self.stop_time = dt.datetime.now()

    def trigger_stop(self):

        current_time = dt.datetime.now()
        if current_time - self.start_time >= duration:
            return True
        else:
            return False
