import logging
from pyoperant import queues, utils

logger = logging.getLogger(__name__)


class Block(queues.BaseHandler):
    """ Class that allows one to iterate over a block of trials according to a
    specific queue.

    Parameters
    ----------
    index: int
        Index of the block
    experiment: instance of Experiment class
        The experiment of which this block is a part
    queue: a queue function or Class
        The queue used to iterate over trials for this block
    conditions: list
        A list of StimulusConditions to iterate over according to the queue
    Additional key-value pairs are used to initialize the trial queue

    Attributes
    ----------

    Examples
    --------

    # Initialize a block with a random queue, and at most 200 trials.
    block = Block(experiment=e,
                  queue=queues.random_queue,
                  conditions=conditions,
                  max_trials=200)
    for trial in block:
        trial.run()
    """

    def __init__(self, index=None, experiment=None, queue=None,
                 conditions=None, **queue_parameters):

        super(Block, self).__init__(queue=queue,
                                    items=conditions,
                                    **queue_parameters)
        self.index = index
        self.experiment = experiment
        self.conditions = conditions

        logger.debug("Initialize block: %s" % self)

    def __str__(self):

        desc = ["Block"]
        if self.conditions is not None:
            desc.append("%d stimulus conditions" % len(self.conditions))
        if self.queue is not None:
            desc.append("queue = %s" % self.queue.__name__)

        return " - ".join(desc)

    def check_completion(self):

        # if self.end is not None:
        #     if utils.check_time((self.start, self.end)): # Will start ever be none? Shouldn't be.
        #         logger.debug("Block is complete due to time")
        #         return True # Block is complete

        # if self.max_trials is not None:
        #     if self.num_trials >= self.max_trials:
        #         logger.debug("Block is complete due to trial count")
        #         return True

        return False

    def __iter__(self):

        # Loop through the queue generator
        trial_index = 0
        for condition in self.queue:
            # Create a trial instance
            trial_index += 1
            trial = Trial(index=trial_index,
                          experiment=self.experiment,
                          condition=condition)
            yield trial


class BlockHandler(queues.BaseHandler):
    """ Class which enables iterating over blocks of trials

    Parameters
    ----------
    blocks: list
        A list of Block objects
    queue: a queue function or Class
        The queue used to iterate over blocks
    Additional key-value pairs are used to initialize the queue

    Attributes
    ----------
    block_index: int
        Index of the current block
    queue: queue generator or class instance
        The queue that will be iterated over.

    Example
    -------
    # Initialize the BlockHandler
    blocks = BlockHandler(blocks, queue=queues.block_queue)
    # Loop through the blocks, then loop through all trials in the block
    for block in blocks:
        for trial in block:
            trial.run()
    """

    def __init__(self, blocks, queue=queues.block_queue, **queue_parameters):

        super(BlockHandler, self).__init__(queue=queue,
                                           items=blocks,
                                           **queue_parameters)
        self.block_index = 0

    def __iter__(self):

        for block in self.queue:
            self.block_index += 1
            block.index = self.block_index
            yield block
