from pyoperant import hwio
from pyoperant.components import Hopper, BaseComponent


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
        BaseComponent.__init__(*args, **kwargs)
        self.lag = 0
        if isinstance(solenoid, hwio.BooleanOutput):
            self.solenoid = solenoid
        else:
            raise ValueError('%s is not an output channel' % solenoid)

    def check(self):
        """Overrides Hopper.check and always returns the status of the solenoid
        """

        print "HopperNoIR.check: Beware, doesn't actually check anything!"
        return self.solenoid.read()
