import logging
import datetime as dt
from pyoperant import hwio, utils
from pyoperant.components import Hopper, BaseComponent

logger = logging.getLogger(__name__)

class HopperNoIR(Hopper):
    """ Class which holds information about a hopper

    Parameters
    ----------
    solenoid : `hwio.BooleanOutput`
        output channel to activate the solenoid & raise the hopper

    Attributes
    ----------
    solenoid : hwio.BooleanOutput
        output channel to activate the solenoid & raise the hopper
    """

    def __init__(self, solenoid, *args, **kwargs):
        logger.debug("Initializing HopperNoIR")
        # super(HopperNoIR, self).__init__(self, *args, **kwargs) # not sure how to resolve this
        BaseComponent.__init__(self, *args, **kwargs)
        self.max_lag = 0
        if isinstance(solenoid, hwio.BooleanOutput):
            self.solenoid = solenoid
        else:
            raise ValueError('%s is not an output channel' % solenoid)

    def __str__(self):

        return "%s: solenoid at %s" % (self.__class__.__name__, self.solenoid)

    def __repr__(self):

        return "%s(%r)" % (self.__class__.__name__, self.solenoid)

    def check(self):
        """Overrides Hopper.check and always returns the status of the solenoid
        """

        logger.debug("No checking configured for %s since there's no input port" % self.__class__.__name__)
        return self.solenoid.read()

    def up(self):
        """Raises the hopper up without checking.
        """

        self.solenoid.write(True)
        return dt.datetime.now()

    def down(self):
        """Lowers the hopper without checking.
        """

        self.solenoid.write(False)
        return dt.datetime.now()
