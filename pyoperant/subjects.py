import os
import csv
import logging

logger = logging.getLogger(__name__)

class Subject(object):

    def __init__(self, name=None, experiment=None,
                 datastore="csv", output_path=None,
                 filename=""):

        logger.debug("Creating subject object for %s" % name)
        self.name = name
        self.experiment = experiment
        self.output_path = output_path

        # The output file where data should be written
        if not filename:
            filename = "%s_trialdata_%s.%s" % (self.name, self.experiment.timestamp, datastore)

        self.filename = os.path.join(self.experiment.parameters["experiment_path"], filename)
        if datastore == "csv":
            self.datastore = CSVStore(self.experiment.fields_to_save, self.filename)
        logger.info("Created subject object with datastore %s" % self.datastore)

    def store_data(self):

        return self.datastore.store(self.experiment.this_trial)

class CSVStore(object):

    def __init__(self, fields_to_save, filename):

        self.filename = filename
        self.fields_to_save = fields_to_save

        with open(self.filename, 'wb') as data_fh:
            trialWriter = csv.writer(data_fh)
            trialWriter.writerow(self.fields_to_save)

    def __str__(self):

        return "CSVStore: filename = %s, fields = %s" % (self.filename, ", ".join(self.fields_to_save))

    def store(self, trial):
        '''write trial results to CSV'''

        trial_dict = {}
        for field in self.fields_to_save:
            try:
                trial_dict[field] = getattr(trial,field)
            except AttributeError:
                trial_dict[field] = trial.annotations[field]
            except KeyError:
                trial_dict[field] = None

        logger.debug("Storing data for trial %d" % trial.index)
        with open(self.filename,'ab') as data_fh:
            trialWriter = csv.DictWriter(data_fh, fieldnames=self.fields_to_save, extrasaction='ignore')
            trialWriter.writerow(trial_dict)

        return True
