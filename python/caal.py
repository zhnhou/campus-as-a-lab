import csv
import numpy as np

__all__ = ['caal_electricity']

class caal_electricity(object):
    def __init__(self, electricity_csv_file):
        with open (electricity_csv_file, 'rb') as csvfile:
            csvReader = csv.reader(csvfile)
            self.csvRawData = list(csvReader)

    def clean_data(self):
        self.
