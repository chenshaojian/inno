# -*- coding: utf-8 -*-
from django.db import models
from mysql_raw import *
import numpy as np
from numpy import *
import datetime
from sklearn.neighbors import KNeighborsClassifier
'''
    训练数据的model

'''
# Create your models here.
MIN_RSSI=100
class LoadData(object):
    """
    数据载入
    属性:
        training_x: 训练的RSSI列表
        training_y: 训练数据标签
        test_x: 测试数据
        test_y: 测试数据标签
    方法:
        get_tra_data: 载入训练数据
        get_test_data: 载入测试数据

    """
    def __init__(self):
        self.training_x = None
        self.training_y = None
        self.test_x = None
        self.test_y = None

    def get_tra_data(self,valid_mbox_ids):
        """
        获取训练数据
        """
        interval = 25
        num_mbox = len(valid_mbox_ids)
        raw_data = self.sqlacs.load_raw_tra_data(valid_mbox_ids)  #载入tb_channel_mbox_template数据载入
        start_t = raw_data[0]['logdate']
        end_t = raw_data[-1]['logdate']
        dur_t = (end_t - start_t).seconds
        tra_data = np.ones((dur_t/interval, num_mbox+1))*MIN_RSSI
        tra_data[:,-1] = 0
        tmp_t = start_t + datetime.timedelta(seconds=interval)
        for row in range(len(tra_data)):
            for i in raw_data:
                t = i['logdate']
                col = valid_mbox_ids.index(i['mbox_serial_num'])
                if (t-tmp_t).seconds <= interval or (tmp_t-t).seconds <= interval:
                    if tra_data[row][col] == MIN_RSSI:
                        tra_data[row][col] = float(i['dbvalue'])
                        tra_data[row][-1] = i['status']
                    else:
                        tra_data[row][col]=(tra_data[row][col]+i['dbvalue'])/2
                        tra_data[row][col]=float('%0.4f'%tra_data[row][col])
            tmp_t = tmp_t + datetime.timedelta(seconds=interval)
        data = []
        for i in tra_data:
            test_mac = np.array(i[:-1])
            if len(test_mac[test_mac==MIN_RSSI]) < 2:
                data.append(i)
        data = np.array(data, dtype=int)
        data = c_[self.datanorm(data[:,:-1]),data[:,-1]]
        self.training_y = data[:,-1]
        self.training_x = data[:,:num_mbox]
        return self.training_x,self.training_y
    def get_test_data(self,valid_mbox_ids,mac=None):
        if mac is None:
            macs = self.ma.load_macs(valid_mbox_ids) #去伪去黑后的mac列表
        else :
            macs = [mac]
        num_mbox = len(valid_mbox_ids)
        interval = 30
        num_staff = 0
        num_machine = 0
        num_other = 0
        store_data = {}
        # 每一mac的数据
        for mac in macs:
            mac_data = self.sqlacs.load_mac_data(mac, valid_mbox_ids)
            mac_st = mac_data[0]['logdate']
            mac_et = mac_data[-1]['logdate']
            mac_durtime = (mac_et - mac_st).seconds
            mac_rows = mac_durtime / interval
            # 增加时差的判断是为了在设备刚刚安装的时候减少设备和工作人员的干扰
            if mac_durtime> 3600*3 or mac_durtime< 120:
                continue
            test_data = ones((mac_rows, num_mbox + 1)) * MIN_RSSI
            test_data = test_data.tolist()
            tmp_t=mac_st+datetime.timedelta(seconds = interval)
            for row in range(mac_rows - 1):
                for i in mac_data:
                    t = i['logdate']
                    col=valid_mbox_ids.index(i['boxid'])
                    if (t - tmp_t).seconds <= interval or (tmp_t-t).seconds <= interval:
                        if test_data[row][col] == MIN_RSSI:
                            test_data[row][col] = i['dbvalue']
                            test_data[row][-1] = tmp_t
                        else:
                            test_data[row][col] = (test_data[row][col]+i['dbvalue'])/2
                    if t > tmp_t + datetime.timedelta(seconds = interval):
                        tmp_t=tmp_t+datetime.timedelta(seconds = interval)
                        break
            # 保留盒子(信号强度<80)数量大于2
            num_rssm70 = 0
            for i in test_data:
                test_rssi = array(i[:-1])
                if len(test_rssi[test_rssi<80]) > (num_mbox-2) and len(test_rssi[test_rssi==MIN_RSSI]) < 2:
                    if store_data.has_key(mac):
                        store_data[mac].append(i)
                    else:
                        store_data[mac] = []
                        store_data[mac].append(i)
                    if len(test_rssi[test_rssi>70]) >= (num_mbox-1):
                        num_rssm70 +=1
            if store_data.has_key(mac):
                if num_rssm70*1.0/len(store_data[mac])>0.75:
                    store_data.pop(mac)
                else:
                    store_data[mac] = array(store_data[mac])
                    store_data[mac][:,:-1] = self.datanorm(store_data[mac][:,:-1])
                    #store_data[mac] = c_[self.datanorm(store_data[mac][:,:-1]),store_data[mac][:,-1]]
        return store_data
    def datanorm(self,dataSet):
        m = dataSet.shape[1]
        meansrssi = dataSet.sum(1)/m
        mdataSet = zeros(shape(dataSet))
        for i in range(m):
            mdataSet[:,i] = meansrssi
        v3 = (dataSet/mdataSet)*60
        extendDaSet = zeros((len(dataSet),m))
        extendDaSet[:,:] = v3
        extendDaSet = np.array(extendDaSet,dtype=int)
        return extendDaSet
class TrainingModel(LoadData):
    """
    机器学习训练模型
    方法:
        knn_model:knn算法
    """
    #def __init__(self,sqlacs, store_id, start_t, end_t, valid_mbox_ids):
    def __init__(self,sqlacs):
        #LoadData.__init__(self)
        self.k = 3
        self.clf = None
        self.pred_y = None
        self.sqlacs = sqlacs
        #self.store_id = store_id
        #self.start_t = start_t
        #self.end_t = end_t
        #self.valid_mbox_ids = valid_mbox_ids
    def knn_model(self,training_x,training_y,test_x):
        self.clf = KNeighborsClassifier(n_neighbors =self.k,weights='distance')
        self.clf.fit(training_x,training_y)
        self.pred_y = self.clf.predict(test_x)
        return self.pred_y
    def training_result(self,area,mac):
        mbox_ids = self.sqlacs.get_raw_mboxs()
        training_x, training_y = self.get_tra_data(mbox_ids)
        mac_data = self.get_test_data(mbox_ids,mac)
        test_xt = np.array(mac_data[mac])
        test_x = test_xt[:,:-1]
        print test_x,training_x,training_y
        self.knn_model(training_x,training_y,test_x)
        p = len(self.pred_y[self.pred_y == area])*100.0 / len(self.pred_y)
        return p





