# -*- coding: utf-8 -*-
from ips_core.models import TrainingModel
from ips_core.mysql_raw import MysqlAccesser,MysqlAccesserRepoert
import datetime
import random
import requests
from multiprocessing import Pool
from sklearn import linear_model
from .report import models

class InnoIps(object):
    """
    inno定位数据
    方法:
        获取在线mbox
        判断盒子数量，选择插值还是计算
    参数:
        store_id: str 店id
        date: datetime 日期
        end_t: datetime 一天的计算结束时间
        start_t: datetime 一天的计算开始时间
        best_tianshu: int 最佳天数
        best_index: int 最佳盒子index
        best_mboxid: str 最佳盒子id
        store_mac_time: dict 店内mac信息, keys为mac , values为时间
        num_valid_mac: int 有效mac数量
        valid_mbox_ids: list 有效盒子
        mbox_ids_num: dict 店内mac信息, keys为mac , values为时间
        sqlacs: 阿里云数据库
        sqlacs_local: 本地报表数据库
        post_data: post的数据


    """
    def __init__(self, store_id, date, sqlacs,sqlacs_local):
        self.store_id = store_id
        self.date = date
        self.sqlacs = sqlacs
        self.sqlacs_local = sqlacs_local

    def insert_mac_data(self,valid_mbox_ids):
        #分类插值方式，全掉线插值和非全掉线插值。
        # 部分掉线
        if len(valid_mbox_ids) > 0:
            best_tianshu, best_index, best_mboxid = self.sqlacs.get_best_mbox(valid_mbox_ids)
        # 全部掉线
        if best_tianshu < 3 or len(valid_mbox_ids) == 0:
            pred_y = self.sqlacs_local.get_insert_random()
        else :
            test_x,training_x,training_dates = self.sqlacs.get_insert_tradata(best_index)
            training_y = self.sqlacs_local.get_insert_training_y(training_dates)
            clf = linear_model.LinearRegression()
            clf.fit(training_x,training_y)
            pred_y = clf.predict([test_x])[0]
        pred_y_keys=pred_y.keys()
        post_data={'average_duration':0,'num_mac':0,'multi_average_duration':0,'first_average_duration':0,\
                'store_id':self.store_id,'date':self.end_t.date(),'num_first_arrival':0,'num_multi_arrival':0,\
                'num_less5Min':0,'num_more30Min':0,'num_betw5_30Min':0}
        for i in pred_y_keys:
            if pred_y[i] < 0:
                post_data[i] = 0
            else:
                post_data[i] = pred_data[i]
        post_data['num_mac']=post_data['num_less5Min']+post_data['num_more30Min']+post_data['num_betw5_30Min']
        r = random.choice(0.7,0.6,0.5,0.8)
        if post_data['num_multi_arrival']>=post_data['num_mac'] or post_data['num_first_arrival']>=post_data['num_mac']:
            post_data['num_multi_arrival'] = random.randint(0,round(r*post_data['num_mac']))
            post_data['num_first_arrival'] = random.randint(0,round((1-r)*post_data['num_mac']))
        elif post_data['num_multi_arrival'] < 5:
            post_data['num_multi_arrival']=random.randint(0,round((1-r)*post_data['num_mac']))
            post_data['num_first_arrival'] = random.randint(0,round(r*post_data['num_mac']))
        post_data['num_first_arrival']=post_data['num_mac']-post_data['num_multi_arrival']
        if post_data['num_first_arrival']<=0:
            post_data['first_average_duration'] = 0
        elif post_data['first_average_duration'] < 30:
            post_data['first_average_duration'] = random.randint(30,50)
        if post_data['num_multi_arrival']<=0:
            post_data['first_average_duration'] = 0
        elif post_data['num_multi_arrival'] <30:
            post_data['num_multi_arrival']= random.randint(30,50)
        post_data['average_duration'] = int((post_data['num_first_arrival']*post_data['first_average_duration']\
                                        +post_data['num_multi_arrival']*post_data['multi_average_duration'])/\
                                        (post_data['num_first_arrival']+post_data['num_multi_arrival']))
        return post_data
    def ips_calculate(self, valid_mbox_ids):
        model = TrainingModel(self.sqlacs)#建立模型
        training_x, training_y = model.get_tra_data(self.store_id, valid_mbox_ids)
        test_mac_data = model.get_test_data(valid_mbox_ids)
        store_mac_time = {}
        for (test_mac,test_data) in test_mac_data.items():
            test_x=test_data[:,:-1]
            test_time=test_data[:,-1]
            pre_y=model.knn_model(training_x,training_y,test_x)#knn定位
            #定位到场外的概率大于80%，或者定位场内的个数少于3个,去除
            if len(pre_y[pre_y==1])*1.0/len(pre_y)>0.8 or len(test_time[pre_y==0])<3:continue
            #计算时长,如果采取时间超过1小时则时间段分为2段
            inter_time=test_time[0]
            durtime = 0
            for i in range(len(test_time)):
                if (test_time[i+1]-test_time[i]).seconds>60*60:
                    durtime = durtime + (test_time[i] - inter_time).seconds
                    inter_time=test_time[i+1]
            durtime = durtime +(test_time[i] - inter_time).seconds
            store_mac_time[test_mac] = durtime/60
        num_valid_mac = len(test_mac_data) #有效未定位的mac数量
        return store_mac_time,num_valid_mac
    def output_data(self, store_mac_time):
        today = start_t.date()
        post_data = {'average_duration':0,'num_mac':0,'multi_average_duration':0,'first_average_duration':0 ,
                   'store_id':self.store_id,'date':str(self.end_t.date()),'num_first_arrival':0,'num_multi_arrival':0,
                   'num_less5Min':0,'num_more30Min':0,'num_betw5_30Min':0}
        first_average_duration = []
        multi_average_duration = []
        for mac in self.store_mac_time:
            if sqlacs.get_indoor_cnt(mac):
                post_data['num_multi_arrival'] = post_data['num_multi_arrival'] + 1
                multi_average_duration = store_mac_time[mac]
            else :
                post_data['num_first_arrival'] = post_data['num_first_arrival'] + 1
                first_average_duration = store_mac_time[mac]
            if store_mac_time[mac] <= 5:
                post_data['num_less5Min'] = post_data['num_less5Min'] + 1
            elif store_mac_time[mac] > 30:
                post_data['num_more30Min'] = post_data['num_more30Min'] + 1
            else:
                post_data['num_betw5_30Min'] = post_data['num_betw5_30Min'] + 1
        post_data['num_mac'] = len(store_data)
        post_data['first_average_duration'] = int(np.average(first_average_duration))
        post_data['multi_average_duration'] = int(np.average(multi_average_duration))
        post_data['average_duration'] = int(np.average(first_average_duration+multi_average_duration))
        return post_data

    def get_valid_mbox_inf(self):
        valid_mbox_ids, mbox_ids_num = sqlacs.get_valid_mbox_inf(self.store_id)
        return valid_mbox_ids, mbox_ids_num

class BlackList(object):
    """
    黑名单
    """
    def __init__(self, sqlacs, store_id=None, date=None, macs=[], mbox_ids=[]):
        self.sqlacs = sqlacs
        self.store_id = store_id
        self.date = date
        self.macs = macs
        self.mbox_ids = mbox_ids
        self.store_cal = []
        pass
    def make_blacklist(self):
        """
        获取所有店及其盒子id
        获取一家店的所有mac
        判断黑名单的mac
        保存数据库
        """
        if self.macs==[] and self.mbox_ids==[]:
            self.mbox_ids = self.sqlacs.get_raw_mboxs(store_id)
            self.macs = self.sqlacs.load_macs(mbox_ids)
        if self.date == None:
            date=datetime.datetime.now().date()-datetime.timedelta(1)
        macs_data = self.sqlacs.get_macs_date_cnt(macs, mbox_ids, date)
        dic={}#{'macid':[出现的天数，规则1天数，规则2天数]}
        #machine:天数超过12天，且大于数量500的天数>总天数-4,采集量小于300的天数<=2
        #staff
        for i in macs_data:
            macid=i[0]
            if not dic.has_key(macid):
                dic[macid]=[0,0,0]
            dic[macid][0]=dic[macid][0]+1
            if int(i[2])>500:
                dic[macid][1]=dic[macid][1]+1
            elif int(i[2])<300 and int(i[2])>20:
                dic[macid][2]=dic[macid][2]+1
        for (mac,rule) in dic.items():
            rules='rule'
            if rule[0]>8:
                if rule[1]>rule[0]-4 and rule[2]<3:
                    rules='machine'
                elif rule[2]>2:
                    rules='staff'
            if rules!='rule':
                '''
                保存数据库
                '''
                sql_str="insert ignore into store_black_staff(storeid,macid,logdate,type) values('%s','%s','%s','%s')"\
                        %(store,mac,date,rules)

    def blacklist(self):
        if self.store_id == None:
            date=datetime.datetime.now().date()-datetime.timedelta(1)
            all_storeid = self.sqlacs.all_storeid()
            p = Pool(2)
            for store_id in all_storeid:
                p.apply_async(self.make_blacklist,args=(store_id,))
            p.close()
            p.join()
            no_cal = [i for i in all_storeid if i not in self.store_cal]
            return no_cal
        else:
            self.make_blacklist()
            return 'ok'

class InnoReport(InnoIps):
    """
    inno报表输出:
        室内定位结果以及摄像头数据
        黑名单筛选
        盒子采集量
        系数值
    """
    def __init__(self, sqlacs, sqlacs_local, store_id=None, date=None):
        InnoIps.__init__(self, store_id, date, sqlacs, sqlacs_local)
        self.date = date
        self.store_id = store_id
        self.sqlacs = sqlacs
        self.sqlacs_local = sqlacs_local
    def mbox_coll_num_rpt(self, mbox_ids_num,valid_mbox_ids):
        '''
        盒子采集量
        字段参数说明:
            storeid: 店id
            date: 日期
            mbox-:盒子采集量
            mbox_id:盒子id列表
            online_num:盒子有效在线个数
        保存数据库
        '''
        mbox_ids = mbox_ids_num.keys()
        mbox_num = mbox_ids_num.values()
        models.Mbox_Collection.objects.update_or_create(storeid=self.store_id,date=self.date,\
                defaults={'mbox1':mbox_num[0],'mbox2':mbox_num[1],'mbox3':mbox_num[2],'mbox4':mbox_num[3],
                'mbox_id':mbox_ids,'online_num':len(valid_mbox_ids)})
    def macfilter_rpt(self, num_valid_mac, num_customer, mbox_ids):
        '''
        参数:
            num_raw_mac : 原始mac数量
            num_valid_mac : 有效mac数量
            num_staff: 工作人员mac数量
            num_machine: 机器mac数量
            num_customer : 定位mac数量
        保存数据库
        '''
        raw_macs = self.sqlacs.load_raw_macs(mbox_ids)
        num_black_mac = self.sqlacs.get_black_mac(raw_macs)
        num_raw_mac = len(raw_macs)
        num_staff, num_machine = num_black_mac['machine'], num_black_mac['staff']
        models.Macfilter.objects.update_or_create(storeid=self.store_id,date=self.date,\
                defaults={'num_raw_mac':num_raw_mac,'num_valid_mac':num_valid_mac,'num_staff':num_staff,\
                'num_machine':num_machine,'num_customer':num_customer})
    def dailyrpt_modify(self,date):
        """
        修订后的周报,增加store_pc
        保存数据库
        """
        store_aveAndmax = self.sqlacs_local.get_history_avgAndmax(date)
        store_macf = self.sqlacs.get_coef()
        #store_id,date,cam_rs,cam_pc,num_mac,average_duration,first_average_duration,multi_average_duration
        #num_first_arrival ,num_multi_arrival,num_betw5_30Min, num_more30Min,num_less5Min
        today_data = self.sqlacs_local.get_today_data(date)
        store_id = today_data[1]; date = today_data[2]; cam_rs = today_data[3]; cam_pc = today_data[4]
        num_mac = today_data[5]; average_duration = today_data[6]; first_average_duration =today_data[7]
        multi_average_duration = today_data[8]; num_first_arrival = today_data[9]; num_multi_arrival = today_data[10]
        num_betw5_30Min = today_data[11]; num_more30Min = today_data[12]; num_less5Min = today_data[13]
        for store in  today_data:
            store_pc = 0
            data=copy(store)
            store_id, num_mac = store[1],store[5]
            if storeid_aveAndmax.has_key(store_id):
                ave_num, max_num = map(float,storeid_aveAndmax[storeid])
                if num_mac>max_num and num_mac<100 and num_mac<ave_num*2:
                    mu = ave_num
                    rate = (num_mac-max_num)/(mu+0.1)
                    rate = min(rate,1.0)
                    storeid_pc = num_mac*(1+rate)
            if storeid_macf.has_key(store_id):
                mac_coef = 1.0
            else:
                mac_coef = storeid_macf[store_id]
            store_pc = int(storeid_pc*mac_coef)
            models.DailyReport_Modify.objects.update_or_create(storeid=store_id,date=date,\
                defaults={'storeid':store_id,'date':date,'cam_rs':cam_rs,'cam_pc':cam_pc,'num_mac':num_mac,
                'storeid_pc':storeid_pc,'average_duration':average_duration,\
                'first_average_duration':first_average_duration,'multi_average_duration':multi_average_duration,
                'num_first_arrival':num_first_arrival,'num_multi_arrival':num_multi_arrival,
                'num_betw5_30Min':num_betw5_30Min,'num_more30Min':num_more30Min,'num_less5Min':num_less5Min})

