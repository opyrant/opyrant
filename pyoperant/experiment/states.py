import logging
import ipdb
from pyoperant import ComponentError, InterfaceError, utils

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

        # ipdb.set_trace()
        self.experiment.session_main()
        return "idle"

    def __exit__(self, type_, value, traceback):

        self.experiment.session_post()

        return super(Session, self).__exit__(type_, value, traceback)


class Idle(State):

    def run(self):

        if self.experiment.check_light_schedule() == False:
            return "sleep"
        elif self.experiment.check_session_schedule():
            return "session"
        else:
            self.experiment.panel.reset()
            logger.debug("idling...")
            utils.wait(self.experiment.parameters["idle_poll_interval"])
            return "idle"


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
