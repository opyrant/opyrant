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
        self.datastore = datastore
        self.output_path = output_path
        self.filename = filename

        self.data = list()
        logger.info("Created subject object with name %s" % self.datastore)

    def create_datastore(self):

        if not self.filename:
            self.filename = "%s_trialdata_%s.%s" % (self.name, self.experiment.timestamp, self.datastore)
        self.filename = os.path.join(self.experiment.parameters["experiment_path"], self.filename)
        if self.datastore == "csv":
            self.datastore = CSVStore(self.experiment.fields_to_save, self.filename)
        logger.info("Created datastore %s for subject %s" % (self.datastore, self.name))

    def store_data(self, trial=None):

        if trial is None:
            trial = self.experiment.this_trial

        trial_dict = {}
        for field in self.experiment.fields_to_save:
            try:
                trial_dict[field] = getattr(trial,field)
            except AttributeError:
                trial_dict[field] = trial.annotations[field]
            except KeyError:
                trial_dict[field] = None

        logger.debug("Storing data for trial %d" % trial.index)
        return self.datastore.store(trial_dict)

class CSVStore(object):

    def __init__(self, fields_to_save, filename):

        self.filename = filename
        self.fields_to_save = fields_to_save

        with open(self.filename, 'wb') as data_fh:
            trialWriter = csv.writer(data_fh)
            trialWriter.writerow(self.fields_to_save)

    def __str__(self):

        return "CSVStore: filename = %s, fields = %s" % (self.filename, ", ".join(self.fields_to_save))

    def store(self, data):
        '''write data results to CSV'''

        with open(self.filename,'ab') as data_fh:
            trialWriter = csv.DictWriter(data_fh, fieldnames=self.fields_to_save, extrasaction='ignore')
            trialWriter.writerow(data)

        return True
