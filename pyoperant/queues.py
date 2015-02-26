import random
import numpy as np
import logging

logger = logging.getLogger(__name__)

def random_queue(items=None, max_items=100):
    """ generator which randomly samples items

    Inputs:
        items (list): A list of items to be queued. Each element of the list can be an item or a 2-tuple of (item, weight) to weight the random choice. If item is a tuple, give each item a weight of 1.
        max_items (int): Maximum number of items to generate. (default: 100)

    Returns:
        A single item at each iteration
    TODO: Might be better to not use numpy. That's a big package. Perhaps only from numpy.random import choice, or something like that.

    """
    if (items is None) or (len(items) == 0):
        logger.debug("random_queue: items must be a list of at least length 1")
        return

    if isinstance(items[0], tuple): # What if the item is a tuple??? MUST FIX
        items, weights = zip(*items)
        items = list(items)
        weights = [float(ww) / np.sum(weights) for ww in weights]

    ii = 0
    while True:
        if (max_items is not None) and (ii >= max_items):
            break
        yield np.random.choice(items, p=weights)
        ii += 1

def block_queue(items=None, repetitions=1, shuffle=False):
    """ generator which samples items in blocks

    Inputs:
        items (list): A list of items to be queued
        repetitions (int): The number of times each item in items will be presented (default: 1)
        shuffle (bool): Shuffles the queue (default: False)
    Returns:
        A single item at each iteration
    TODO: Currently first expands the list of items 'repetitions' times. This should be done in the iteration loop, ideally.
    """
    items_repeated = []
    for rr in range(repetitions):
        items_repeated += items
    items = items_repeated

    if shuffle:
        random.shuffle(items)

    for item in items:
        yield item

def staircase_queue(experiment,
                    start,
                    up=1,
                    down=3,
                    step=1.0,
                    min_val=None,
                    max_val=None,
                    tr_min=0,
                    tr_max=100,
                    reversals=None,
                    ):
    """ generates trial conditions for a staircase procedure

    This procedure returns values for each trial and assumes that larger values are
    easier. Thus, after a correct trial, the next value returned will be smaller and
    after incorrect trials, the next value returned will be larger. The magnitudes of
    these changes are down*step and up*step, respectively.

    Args:
        experiment (Experiment):  experiment object to keep track of last trial accuracy
        start (float/int): the starting value of the procedure

    Kwargs:
        up (int): number of steps to take after incorrect trial (default: 1)
        down (int): number of steps to take after correct trial (default: 3)
        step (float): size of steps (default: 1.0)
        shuffle (bool): Shuffles the queue (default: False)
        min_val (float): minimum parameter value to allow (default: None)
        max_val (float): maximum parameter value to allow (default: None)
        tr_min (int): minimum number of trials (default: 0)
        tr_max (int): maximum number of trials (default: 100)
    Returns:
        float

    """
    val = start
    # first trial, don't mess with checking
    yield val
    tr_num = 1
    nrev = 0
    going_up = False
    cont = True

    # subsequent trials
    while cont:

        last = experiment.trials[-1]

        # staircase logic
        if last.correct:
            chg = -1 * down
        else:
            chg = up
        val += float(step) * chg

        # check for reversal
        if last.correct==going_up: # checks if last trial's perf was consistent w/ trend
            nrev += 1
            going_up = not going_up

        # stop at max/min if we hit the rails
        if (max_val!=None) and (val > max_val):
            val = max_val
        elif (min_val!=None) and (val < min_val):
            val = min_val

        yield val

        # decide whether to stop iterating
        tr_num += 1
        if tr_num < tr_min:
            cont = True
        elif tr_num >= tr_max:
            cont = False
        elif nrev >= reversals:
            cont = False

class BaseHandler(object):

    def __init__(self, queue=random_queue, items=None, weights=None, queue_parameters=None):

        if queue_parameters is None:
            queue_parameters = dict()

        if queue is random_queue:
            if weights is not None:
                items = zip(items, weights)

        if not hasattr(queue, "__call__"):
            raise TypeError("queue must be a callable function")

        self.queue = queue(items=items, **queue_parameters)

    def __iter__(self):

        for item in self.queue:
            yield item
