

class Stimulus(Event):
    """docstring for Stimulus"""
    def __init__(self, *args, **kwargs):
        super(Stimulus, self).__init__(*args, **kwargs)
        if self.label=='':
            self.label = 'stimulus'

class AuditoryStimulus(Stimulus):
    """docstring for AuditoryStimulus"""
    def __init__(self, *args, **kwargs):
        super(AuditoryStimulus, self).__init__(*args, **kwargs)
        if self.label=='':
            self.label = 'auditory_stimulus'

class StimulusCondition(object):

    def __init__(self, name="", response=None, rewarded=True, punished=True, file_path=None, recursive=False):

        if file_path is None:
            print("file_path must be specified!")
            return

        if not os.path.exist(file_path):
            print("file_path does not exist!")
            return

        self.name = name
        self.response = response
        self.rewarded = rewarded
        self.punished = punished
        self.file_path = file_path
        self.recursive = recursive
        self.files = os.path.walk(self.file_path, self._filter, None)

    @staticmethod
    def _filter(arg, dirname, fnames):

        pass

    def get(self, replacement=True):

        index = random.choice(range(len(self.files)))
        if replacement:
            return self.files[index]
        else:
            return self.files.pop(index)
