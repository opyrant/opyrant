import logging
from pyoperant import queues, utils

logger = logging.getLogger(__name__)


class Trial(object):
    """ Class that implements all basic functionality of a trial

    Parameters
    ----------
    index: int
        Index of the trial
    experiment: instance of Experiment class
        The experiment of which this trial is a part
    condition: instance of StimulusCondition
        The condition for the current trial. Provides the trial with a stimulus,
        as well as reinforcement instructions

    Attributes
    ----------
    index: int
        Index of the trial
    experiment: instance of Experiment class
        The experiment of which this trial is a part
    stimulus_condition: instance of StimulusCondition
        The condition for the current trial. Provides the trial with a stimulus,
        as well as reinforcement instructions

    Methods
    -------
    run()
        Runs the trial
    """
    def __init__(self,
                 index=None,
                 experiment=None,
                 condition=None,
                 *args, **kwargs):

        super(Trial, self).__init__(*args, **kwargs)
        self.index = index

        # Object references
        self.experiment = experiment
        self.condition = condition

        # Trial statistics
        self.stimulus = None
        self.response = None
        self.correct = None
        self.rt = None
        self.reward = False
        self.punish = False

    def run(self):
        """ Runs the trial

        Summary
        -------
        The main structure is as follows:

        Get stimulus -> Initiate trial -> Play stimulus -> Receive response ->
        Consequate response -> Finish trial -> Save data.

        The stimulus, response and consequate stages are broken into pre, main,
        and post stages. Only use the stages you need in your experiment.
        """

        self.experiment.this_trial = self

        # Get the stimulus
        self.stimulus = self.condition.get()

        # Any pre-trial logging / computations
        self.experiment.trial_pre()

        # Perform stimulus playback
        self.experiment.stimulus_pre()
        self.experiment.stimulus_main()
        self.experiment.stimulus_post()

        # Evaluate subject's response
        self.experiment.response_pre()
        self.experiment.response_main()
        self.experiment.response_post()

        # Consequate the response with a reward, punishment or neither
        self.experiment.consequate_pre()
        self.experiment.consequate_main()
        self.experiment.consequate_post()

        # Finalize trial
        self.experiment.trial_post()

        # Store trial data
        self.experiment.subject.store_data(self)


class TrialHandler(queues.BaseHandler):
    """ Provides an iterator for looping through trials according to a given
    queue.

    Parameters
    ----------
    block: instance of the Block class
        The block in which these trials will be run. Defines a list of
        conditions, a queue, and a list of weights for each condition.

    Attributes
    ----------
    block: instance of the Block class
        The block in which these trials will be run. Defines a list of
        conditions, a queue, and a list of weights for each condition.
    trial_index: int
        The index of the current trial
    queue: instance of a queue
        The instance of a queue initialized from the data in block

    Example
    -------
    # Initialize a TrialHandler
    trials = TrialHandler(block)
    # Loop through the trials and run each one
    for trial in trials:
        trial.run()
    """

    def __init__(self, block):

        super(TrialHandler, self).__init__(queue=block.queue,
                                           items=block.conditions,
                                           weights=block.weights,
                                           queue_parameters=block.queue_parameters)
        self.block = block
        self.trial_index = 0

    def __iter__(self):

        # Loop through the queue iterator
        for condition in self.queue:
            # Create a trial instance
            self.trial_index += 1
            trial = Trial(index=self.trial_index,
                          experiment=self.block.experiment,
                          condition=condition)
            yield trial
