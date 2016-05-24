import csv
import numpy as np
from astropy.time import Time


__all__ = ['caal_electricity']

class caal_electricity(object):
    def __init__(self, electricity_csv_file):
        self.missval = long(-1000000)
        with open (electricity_csv_file, 'rb') as csvfile:
            csvReader = csv.reader(csvfile)
            tmp = list(csvReader)
            self.csvRawData = np.array(tmp)[1:]
            self.header = np.array(tmp[0])
            del tmp

    def clean_data(self):
        print "clean"

    def get_bd_id(self):
        ip_bd_id = np.where(self.header == 'BD_ID')[0][0]
        self.bd_id = np.unique(self.csvRawData[:,ip_bd_id])

    def get_meter_id(self):
        ip_meter_id = np.where(self.header == 'METER_ID')[0][0]
        self.meter_id, self.meter_index, self.meter_counts = np.unique(self.csvRawData[:,ip_meter_id], return_index=True, return_counts=True)

    def get_meter_data(self, meter_id):
        ip_tmp = np.where(self.meter_id == meter_id)[0][0]
        ip_usage = np.where(self.header == 'USAGE')[0][0]
        ip_temp  = np.where(self.header == 'TEMPERATURE')[0][0]
        ip_datetime = np.where(self.header == 'DATETIME')[0][0]

        ip_meter = self.meter_index[ip_tmp]
        counts   = self.meter_counts[ip_tmp]

        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_usage]
        usage_list = [float(i) if i != "" else self.missval for i in tmp]

        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_temp]
        temp_list = [float(i) if i != "" else self.missval for i in tmp]

        # here we convert the date time to modified Julian date
        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_datetime]
        datetime_list = [Time(i.replace(" ","T")).mjd for i in tmp]


