from opyrant import utils, components
from opyrant.behavior import base

class Lights(base.BaseExp):
    """docstring for Lights"""
    def __init__(self,  *args, **kwargs):
        super(Lights, self).__init__(*args, **kwargs)

    def panel_reset(self):
        try:
            self.panel.reset()
        except components.HopperWontDropError:
            pass
