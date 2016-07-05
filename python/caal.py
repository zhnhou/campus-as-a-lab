import os
import pandas as pd
import numpy as np
import cPickle as pickle
from astropy.time import Time

# need more comments to explain the codes

__all__ = ['caal_electricity']

class caal_electricity(object):
    def __init__(self, electricity_csv_file, cache_file=None):

        self.missval = -1.00E30

        if (cache_file is None):
            i = electricity_csv_file.rfind('/')
            cache_path = electricity_csv_file[0:i+1]

            n = len(electricity_csv_file)
            self.cache_file = cache_path+'cache_'+electricity_csv_file[i+1:n-4]+'.pkl'
        else:
            self.cache_file = cache_file

        self.csvRawData = pd.read_csv(electricity_csv_file, skip_blank_lines=True)
        self.header = list(self.csvRawData.columns)
        
        self.read_bd_id()
        self.read_meter_id()

        start_ = []
        end_ = []

        for meter_id in self.meter_id:
            start, end = self.get_meter_startend(meter_id)
            start_.append(start)
            end_.append(end)

        self.start_date = min(start_)
        self.end_date   = max(end_)

        self.delta_t = 0.50e0/24.00e0
        self.num_data_point = int((self.end_date - self.start_date)/self.delta_t + 1)

    ## get all the bd_id in csv file as an array of strings
    def read_bd_id(self):
        self.bd_id = np.unique(self.csvRawData.BD_ID)
        self.num_bd = self.bd_id.shape

    ## get all the meter_id in csv file as an array of strings
    def read_meter_id(self):
        self.meter_id = np.unique(self.csvRawData.METER_ID)

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

        print "start reading data from building "+bd_id
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

    ## This method will take a glance of the size of the meter data
    def get_meter_startend(self, meter_id):

        tmp = self.csvRawData.loc[self.csvRawData.METER_ID == meter_id]
        start_date = Time(tmp.DATETIME.iloc[0]).mjd
        end_date = Time(tmp.DATETIME.iloc[-1]).mjd

        print end_date
        
        return start_date, end_date

    ## this method is the core of the class, getting the data points
    ## of the meter of given meter_id
    ## the building information such as lon, lat and building name
    ## are also included
    def get_meter_data(self, meter_id):

        print "    start reading Meter data - "+meter_id
        
        tmp = self.csvRawData.loc[self.csvRawData.METER_ID == meter_id]
        usage_array= tmp.USAGE.values
        num_missval_usage = tmp.isnull().sum().USAGE
        usage_array[np.isnan(usage_list)] = self.missval

        temp_array = tmp.TEMPERATURE.values
        num_missval_temp = tmp.isnull().sum().TEMPERATURE
        temp_array[np.isnan(temp_list)] = self.missval

        # here we convert the date time to modified Julian date
        datetime_array = np.asarray([Time(i).mjd for i in tmp.DATETIME])

        ## here lon, lat, and des are scalars
        lon = tmp.CLON.iloc[0]
        lat = tmp.CLAT.iloc[0]
        des = tmp.DISCRIPT1.iloc[0]

        num_stamp = usage_array.shape[0]

        del tmp

        print "    fetched meter "+meter_id+" "+str(num_stamp)+" data points"
        print " "

        d = {'num_data_point':num_stamp, 'usage':usage_array, 'temperature':temp_array, 'datetime':datetime_array, 
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

        
        
        
        
