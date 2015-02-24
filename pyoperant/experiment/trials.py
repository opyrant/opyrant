from pyoperant.utils import Event

class Trial(Event):
    """docstring for Trial"""
    def __init__(self,
                 index=None,
                 experiment=None,
                 stimulus_condition=None,
                 *args, **kwargs):

        super(Trial, self).__init__(*args, **kwargs)
        self.label = 'trial'
        self.index = index

        # Object references
        self.experiment = experiment
        self.condition = stimulus_condition

        # Trial statistics
        self.stimulus = None
        self.response = None
        self.correct = None
        self.rt = None
        self.reward = False
        self.punish = False

    def run(self):
        """
        This is where the basic trial structure is encoded. The main structure
        is as follows: Get stimulus -> Initiate trial -> Play stimulus ->
        Receive response ->  Consequate response -> Finish trial -> Save data.
        The stimulus, response and consequate stages are broken into pre, main,
        and post stages. This seems a bit too subdivided, and it may be, but a
        pre and post stage allow for a clean place to put delays between stages.
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
        self.experiment.subject.store_data()


class Block(Event):

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

    def check_completion(self):

        if self.end is not None:
            if utils.check_time((self.start, self.end)): # Will start ever be none? Shouldn't be.
                return True # Block is complete

        if self.max_trials is not None:
            if self.num_trials >= self.max_trials:
                return True

        return False
