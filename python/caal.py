import os

# now we use pandas to read csv file
#import csv
import pandas as pd

import numpy as np
import cPickle as pickle
from astropy.time import Time

# need more comments to explain the codes

__all__ = ['caal_electricity']

class caal_electricity(object):
    def __init__(self, electricity_csv_file, cache_file=None):
#        self.missval = long(-1000000)

        if (cache_file is None):
            i = electricity_csv_file.rfind('/')
            cache_path = electricity_csv_file[0:i+1]

            n = len(electricity_csv_file)
            self.cache_file = cache_path+'cache_'+electricity_csv_file[i+1:n-4]+'.pkl'
        else:
            self.cache_file = cache_file

#        with open (electricity_csv_file, 'rb') as csvfile:
#            csvReader = csv.reader(csvfile)
#            tmp = list(csvReader)

        self.csvRawData = pd.read_csv(electricity_csv_file, skip_blank_lines=True)
        self.header = list(self.csvRawData.columns)
        
        self.read_bd_id()
        self.read_meter_id()

    ## get all the bd_id in csv file as an array of strings
    def read_bd_id(self):
#        ip_bd_id = np.where(self.header == 'BD_ID')[0][0]
#        self.bd_id = np.unique(self.csvRawData[:,ip_bd_id])
        self.bd_id = np.unique(self.csvRawData.BD_ID)
        self.num_bd = self.bd_id.shape

    ## get all the meter_id in csv file as an array of strings
    def read_meter_id(self):
        ip_meter_id = np.where(self.header == 'METER_ID')[0][0]
        self.meter_id, self.meter_index, self.meter_counts = np.unique(self.csvRawData[:,ip_meter_id], return_index=True, return_counts=True)

    ## get all the data points organized within a dictionary with
    ## bd_id as the keys
    def get_all_bd_data(self):
        bd_data_all = {}
        for bd_id in self.bd_id:
            bd_data = self.get_bd_data(bd_id)

            bd_data_all[bd_id] = bd_data

        return bd_data_all


    ## get the meter data within one building by given bd_id
    def get_bd_data(self, bd_id):
        bd_meter_id = self.get_bd_meter(bd_id)
        
        num_meter_bd = np.shape(bd_meter_id)[0]

        num_missval_usage = np.zeros(num_meter_bd, dtype=np.int32)
        num_missval_temp  = np.zeros(num_meter_bd, dtype=np.int32)

        for i in np.arange(0,num_meter_bd):
            meter_data = self.get_meter_data(bd_meter_id[i])

            num_missval_usage[i] = meter_data['num_missval_usage']
            num_missval_temp[i]  = meter_data['num_missval_temp']

            if i==0:
                num_data_point = meter_data['num_data_point']
                usage_bd = np.zeros( (num_data_point, num_meter_bd) )
                temp_bd  = np.zeros(num_data_point)
                datetime = np.zeros(num_data_point)

                temp_bd[:] = meter_data['temperature'][:]
                datetime[:] = meter_data['datetime']

                lon = meter_data['CLON']
                lat = meter_data['CLAT']
                descr = meter_data['DESCRIPT']

            if i > 0:
                if (lon != meter_data['CLON'] or lat != meter_data['CLAT']):
                    print "different lon/lat between meters within building "+bd_id
                    exit()

                if (num_data_point != meter_data['num_data_point']):
                    print "different number of data points between meters within building "+bd_id
                    exit()

                temp_equal = np.array_equal(temp_bd, np.asarray(meter_data['temperature']))
                time_equal = np.array_equal(datetime, np.asarray(meter_data['datetime']))

                if (not temp_equal):
                    print "temperature measures are different between meters within building "+bd_id
                    exit()
                if (not time_equal):
                    print "time stamps are different between meters within building "+bd_id
                    exit()

            usage_bd[:,i] = meter_data['usage'][:]

            del meter_data

        bd_data = {'num_meter':num_meter_bd, 'num_data_point_per_meter':num_data_point, 'meter_id':bd_meter_id,
                   'datetime':datetime, 'usage':usage_bd, 'temperature':temp_bd, 'bd_name':descr, 'CLON':lon, 'CLAT':lat,
                   'num_missval_usage':num_missval_usage, 'num_missval_temp':num_missval_temp}

        return bd_data


    ## in this method we collect the meter_id for each bd_id,
    ## several bd_id have multiple meters in its building
    def get_bd_meter(self, bd_id):
        meter_bd = []
        for i in self.meter_id:
            if (i[0:len(bd_id)] == bd_id):
                meter_bd.append(i)

        return meter_bd

    ## this method is the core of the class, getting the data points
    ## of the meter of given meter_id
    ## the building information such as lon, lat and building name
    ## are also included
    def get_meter_data(self, meter_id):
        
        ip_tmp = np.where(self.meter_id == meter_id)[0][0]
        ip_usage = np.where(self.header == 'USAGE')[0][0]
        ip_temp  = np.where(self.header == 'TEMPERATURE')[0][0]
        ip_datetime = np.where(self.header == 'DATETIME')[0][0]

        ip_lon = np.where(self.header == 'CLON')[0][0]
        ip_lat = np.where(self.header == 'CLAT')[0][0]
        ip_des = np.where(self.header == 'DISCRIPT1')[0][0]

        ip_meter = self.meter_index[ip_tmp]
        counts   = self.meter_counts[ip_tmp]

        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_usage]
        usage_list = [float(i) if i != "" else self.missval for i in tmp]
        num_missval_usage = usage_list.count(self.missval)

        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_temp]
        temp_list = [float(i) if i != "" else self.missval for i in tmp]
        num_missval_temp = temp_list.count(self.missval)

        # here we convert the date time to modified Julian date
        tmp = self.csvRawData[ip_meter:ip_meter+counts, ip_datetime]
        datetime_list = [Time(i.replace(" ","T")).mjd for i in tmp]

        lon = self.csvRawData[ip_meter, ip_lon]
        lat = self.csvRawData[ip_meter, ip_lat]
        des = self.csvRawData[ip_meter, ip_des]

        num_stamp = np.shape(usage_list)[0]

        print "fetched meter "+meter_id+" "+str(num_stamp)+" data points"

        d = {'num_data_point':num_stamp, 'usage':usage_list, 'temperature':temp_list, 'datetime':datetime_list, 
             'CLON':lon, 'CLAT':lat, 'DESCRIPT':des, 'num_missval_usage':num_missval_usage, 'num_missval_temp':num_missval_temp}

        self.check_time_stamp(d)

        return d

    def check_time_stamp(self, meter_data):

        num_stamp = meter_data['num_data_point']

        t_first = meter_data['datetime'][0]
        t_last  = meter_data['datetime'][num_stamp-1]

        delta_t = 0.5/24.00

        t_array = np.arange(0,num_stamp) * delta_t + t_first
        t_diff = meter_data['datetime'] - t_array

        for i in np.arange(0, num_stamp):
            t_diff[i] = round(t_diff[i]/delta_t)

        diff = [ int(i) for i in np.unique(t_diff)]

        if (np.shape(diff)[0] == 1 and diff[0] == 0):
            return 0
        else:
            return diff

        
        
        
        
