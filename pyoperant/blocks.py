import logging
from pyoperant import queues, utils

logger = logging.getLogger(__name__)
# TODO: Document Block and BlockHandler objects
# TODO: How do these objects work? What is a block? What are they used for?

class Block(utils.Event):

    def __init__(self, index=None, experiment=None, queue=None, queue_parameters=None,
                 reinforcement=None, conditions=None, weights=None, max_trials=None,
                 *args, **kwargs):

        super(Block, self).__init__(*args, **kwargs)
        self.index = index
        self.experiment = experiment
        self.queue = queue
        self.queue_parameters = queue_parameters
        self.reinforcement = reinforcement
        self.conditions = conditions
        self.weights = weights
        self.max_trials = max_trials

        logger.debug("Initialize block: %s" % self)

    def __str__(self):

        desc = ["Block"]
        if self.conditions is not None:
            desc.append("%d stimulus conditions" % len(self.conditions))
        if self.queue is not None:
            desc.append("queue = %s" % self.queue.__name__)
        if self.reinforcement is not None:
            desc.append("reinforcement = %s" % self.reinforcement.__class__.__name__)

        return " - ".join(desc)

    def check_completion(self):

        if self.end is not None:
            if utils.check_time((self.start, self.end)): # Will start ever be none? Shouldn't be.
                logger.debug("Block is complete due to time")
                return True # Block is complete

        if self.max_trials is not None:
            if self.num_trials >= self.max_trials:
                logger.debug("Block is complete due to trial count")
                return True

        return False


class BlockHandler(queues.BaseHandler):

    def __init__(self, blocks=None, weights=None,
                 queue=queues.block_queue, queue_parameters=None):

        super(BlockHandler, self).__init__(queue=queue,
                                           items=blocks,
                                           weights=weights,
                                           queue_parameters=queue_parameters)
        self.block_id = 0

    def __iter__(self):

        for block in self.queue:
            self.block_id += 1
            block.index = self.block_id
            yield block
