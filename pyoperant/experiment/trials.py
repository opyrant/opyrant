class Trial(Event):
    """docstring for Trial"""
    def __init__(self,
                 index=None,
                 experiment=None,
                 block=None,
                 stimulus_condition=None,
                 subject=None,
                 *args, **kwargs):
        super(Trial, self).__init__(*args, **kwargs)
        self.label = 'trial
        self.index = index

        # Object references
        self.experiment = experiment
        self.block = block
        self.stimulus_condition = stimulus_condition
        self.subject = subject

        self.stimulus = None
        self.response = None
        self.correct = None
        self.rt = None
        self.reward = False
        self.punish = False
        self.events = []
        self.stim_event = None

    def run(self):

        # Get the stimulus
        self.stimulus = self.stimulus_condition.get()

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
        self.subject.store_data()


class Block(Event):

    def __init__(self, index=None):

        super(Block, self).__init__(*args, **kwargs)
        self.index = index
        self.trials = None

    def schedule(self, start, end):

        self.start = start
        self.end = end
