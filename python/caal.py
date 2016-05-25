import os
import csv
import numpy as np
import cPickle as pickle
from astropy.time import Time


__all__ = ['caal_electricity']

class caal_electricity(object):
    def __init__(self, electricity_csv_file, cache_file=None):
        self.missval = long(-1000000)

        if (cache_file is None):
            i = electricity_csv_file.rfind('/')
            cache_path = electricity_csv_file[0:i+1]

            n = len(electricity_csv_file)
            self.cache_file = cache_path+'cache_'+electricity_csv_file[i+1:n-4]+'.pkl'
        else:
            self.cache_file = cache_file

        with open (electricity_csv_file, 'rb') as csvfile:
            csvReader = csv.reader(csvfile)
            tmp = list(csvReader)

        self.csvRawData = np.array(tmp)[1:]
        self.header = np.array(tmp[0])

    def clean_data(self):
        print "clean"

    def read_bd_id(self):
        ip_bd_id = np.where(self.header == 'BD_ID')[0][0]
        self.bd_id = np.unique(self.csvRawData[:,ip_bd_id])
        self.num_bd = self.bd_id.shape

    def read_meter_id(self):
        ip_meter_id = np.where(self.header == 'METER_ID')[0][0]
        self.meter_id, self.meter_index, self.meter_counts = np.unique(self.csvRawData[:,ip_meter_id], return_index=True, return_counts=True)


    ## in this method we collect the meter_id for each bd_id,
    ## several bd_id have multiple meters in its building
    def get_bd_meter(self, bd_id):
        meter_bd = []
        for i in self.meter_id:
            if (i[0:len(bd_id)] == bd_id):
                meter_bd.append(i)

        return meter_bd


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

        num_stamp = np.shape(usage_list)[0]

        d = {'num_data_point':num_stamp, 'usage':usage_list, 'temperature':temp_list, 'datetime':datetime_list}

        return d


        
