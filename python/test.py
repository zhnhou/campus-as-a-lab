from caal import *
import cPickle as pickle
import matplotlib.pyplot as plt

#csvfile = '/project/kicp/zhenhou/projects/caal/test.csv'
csvfile = '/project/kicp/zhenhou/projects/caal/campus_buildings_geo_meters_data.csv'

ca = caal_electricity(csvfile)

m0 = ca.get_meter_data('A06_B1')
plt.plot(ca.datetime, m0['usage'])

#bd_data_all = ca.get_all_bd_data()
#cache_file = '/project/kicp/zhenhou/projects/caal/cache_campus_buildings_geo_meters_data.pkl'
#with open(cache_file, "wb") as cache:
#    pickle.dump(bd_data_all, cache)
