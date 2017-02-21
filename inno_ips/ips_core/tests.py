from django.test import TestCase
from models import LoadData
from mysql_raw import *
# Create your tests here.
if __name__ == '__main__':
#    a = LoadData()
#    store_id=982
#    mbox_ids=['20160514', '20161564', '20161063', '20161265']
#    print a.get_tra_data(store_id, mbox_ids)
    store_id = 460
    mbox_ids=['20160514', '20161564', '20161063', '20161265']
    min_time='2017-01-17 17:10:00'
    max_time='2017-01-17 17:35:00'
    a = MysqlAccesser()
    print a.load_macs(min_time,max_time,store_id,mbox_ids)


