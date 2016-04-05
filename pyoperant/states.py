import logging
import numpy as np
from pyoperant import (EndSession,
                       EndExperiment,
                       ComponentError,
                       InterfaceError,
                       utils)

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
    """ States provide a nice interface for running experiments and transitioning to sleep/idle phases. By implementing __enter__ and __exit__ methods, they use the "with" statement construct that allows for simple error handling (e.g. session ends, keyboard interrupts to stop an experiment, etc.)

    Parameters
    ----------
    schedulers: list of scheduler objects
        These determine whether or not the state should be running, using their check method

    Methods
    -------
    check() - Check if the state should be active according to its schedulers
    run() - Run the state
    """

    def __init__(self, experiment=None, schedulers=None):

        if schedulers is None:
            schedulers = list()
        self.schedulers = schedulers
        self.experiment = experiment

    def check(self):

        # If any scheduler says not to run, then don't run
        for scheduler in self.schedulers:
            if not scheduler.check():
                return False

        return True

    def __enter__(self):

        logger.info("Entering %s state" % self.__class__.__name__)
        for scheduler in self.schedulers:
            scheduler.start()

        return self

    def __exit__(self, type_, value, traceback):

        logger.info("Exiting %s state" % self.__class__.__name__)
        for scheduler in self.schedulers:
            scheduler.stop()
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
    """ Session state for running an experiment. Should be used with the "with" statement (see Examples).

    Parameters
    ----------
    schedulers: list of scheduler objects
        These determine whether or not the state should be running, using their check method
    experiment: an instance of a Behavior class
        The experiment whose session methods should be run.

    Methods
    -------
    check() - Check if the state should be active according to its schedulers
    run() - Run the experiment's session_main method

    Examples
    --------
    with Session(experiment=experiment) as state: # Runs experiment.session_pre
        state.run() # Runs experiment.session_main
    # Exiting with statement runs experiment.session_post
    """

    def __enter__(self):

        self.experiment.session_pre()
        for scheduler in self.schedulers:
            scheduler.start()

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
    """ A simple idle state.

    Parameters
    ----------
    experiment: an instance of a Behavior class
        The experiment whose session methods should be run.
    poll_interval: int
        The interval, in seconds, at which other states should be checked to run

    Methods
    -------
    check() - Check if the state should be active according to its schedulers
    run() - Run the experiment's session_main method

    Examples
    --------
    with Session(experiment=experiment) as state: # Runs experiment.session_pre
        state.run() # Runs experiment.session_main
    # Exiting with statement runs experiment.session_post
    """
    def __init__(self, experiment=None, poll_interval=60):

        super(Idle, self).__init__(experiment=experiment,
                                   schedulers=None)
        self.poll_interval = poll_interval

    def run(self):

        while True:
            for state in self.experiment.states:
                state.check()
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


class TimeOfDayScheduler(object):
    """ Schedule a state to start and stop depending on the time of day

    Parameters
    ----------
    time_periods: string or list
        The time periods in which this schedule should be active. The value of "sun" can be passed to use the current day-night schedule. Otherwise, pass a list of tuples (start, end) (e.g. [("5:00", "17:00")] for 5am to 5pm)

    Methods
    -------
    check() - Returns True if the state should be active according to this schedule
    """

    def __init__(self, time_periods="sun"):

        self.time_periods = time_periods

    def start(self):

        pass

    def stop(self):

        pass

    def check(self):
        """ Returns True if the state should be active according to this schedule
        """

        return utils.check_time(self.time_periods)


class TimeScheduler(object):
    """ Schedules a state to start and stop based on how long the state has been active and how long since the state was previously active.

    Parameters
    ----------
    duration: int
        The duration, in minutes, that the state should be active
    interval: int
        The time since the state was last active before it should become active again.

    Methods
    -------
    start() - Stores the start time of the current state
    stop() - Stores the end time of the current state
    check() - Returns True if the state should activate
    """
    def __init__(self, duration=0, interval=0):

        self.duration = duration
        self.interval = interval

        self.start_time = None
        self.stop_time = None

    def start(self):
        """ Stores the start time of the current state """

        self.start_time = dt.datetime.now()
        self.stop_time = None

    def stop(self):
        """ Stores the end time of the current state """

        self.stop_time = dt.datetime.now()
        self.start_time = None

    def check(self):

        current_time = dt.datetime.now()
        # If start_time is None, the state is not active. Should it be?
        if self.start_time is None:
            # No interval specified, always start
            if self.interval <= 0:
                return True

            # The state hasn't activated yet, always start
            if self.stop_time is None:
                return True

            # Has it been greater than interval minutes since the last time?
            if current_time - self.stop_time >= interval:
                return True

        # If stop_time is None, the state is currently active. Should it stop?
        if self.stop_time is None:
            # No duration specified, so do not stop
            if self.duration <= 0:
                return True

            # Has the state been active for long enough?
            if current_time - self.start_time >= duration:
                return True

        return False
