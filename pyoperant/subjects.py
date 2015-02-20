

class Subject(object):

    def __init__(name=None, datastore="csv", output_path=None):

        self.name = name
        self.datastore = datastore
        self.output_path = output_path
        # The output file where data should be written
        csv_filename = "%s_trialdata_%s.csv" % (self.parameters["subject"], self.timestamp)
        self.data_csv = os.path.join(self.parameters['experiment_path'], csv_filename)
        if self.datastore.lower() == "csv":
            self.make_data_csv()

    def make_data_csv(self):
        """ Create the csv file to save trial data

        This creates a new csv file at experiment.data_csv and writes a header row
        with the fields in experiment.fields_to_save
        """
        with open(self.data_csv, 'wb') as data_fh:
            trialWriter = csv.writer(data_fh)
            trialWriter.writerow(self.fields_to_save)

    def save_trial(self,trial):
        '''write trial results to CSV'''

        trial_dict = {}
        for field in self.fields_to_save:
            try:
                trial_dict[field] = getattr(trial,field)
            except AttributeError:
                trial_dict[field] = trial.annotations[field]

        with open(self.data_csv,'ab') as data_fh:
            trialWriter = csv.DictWriter(data_fh,fieldnames=self.fields_to_save,extrasaction='ignore')
            trialWriter.writerow(trial_dict)
