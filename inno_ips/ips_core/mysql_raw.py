 # -*- coding: utf-8 -*-
import MySQLdb as mdb
import MySQLdb.cursors
import datetime
import numpy as np
import re
import random

host1 = 'rdsiyj2ynqumiej.mysql.rds.aliyuncs.com'
usr1 = 'rdcenter'
pwd1 = 'RD123456789'
db1 = 'mbox_web'
class MysqlAccesserRepoert(object):
    def __init__(self, start_t=None, end_t = None, store_id=None):
        self.host = ''
        self.usr = 'root'
        self.pwd = 'inno'
        self.db = 'data_manager'
        self.conn = mdb.connect(self.host, self.usr, self.pwd, self.db)
        self.cur = self.conn.cursor(cursorclass=mdb.cursors.DictCursor)
        self.store_id = store_id
        self.start_t = start_t
        self.end_t = end_t
    def sql_close(self):
        self.conn.commit()
        self.cur.close()
        self.cur.close()
        self.conn.close()
    def get_insert_random(self):

        sql_str = "select * from store_id,date,num_mac,average_duration,first_average_duration,\
                multi_average_duration,num_first_arrival,num_multi_arrival,num_betw5_30Min,num_more30Min,num_less5Min\
                from mbox_dailyreport2 where store_id='%s' order by rand() limit 1 "%(dates,self.store_id)
        self.cur.execute(sql_str)
        pred_y = self.cur.fetchall()[0]
        if pred_y[0]<10:
            r = random.choice([0.4,0.6,1.4,1.6])
        else:
            r = random.choice([0.7,0.8,1.2,1.3])
        pred_y['num_mac'] = pred_y['num_mac']*r #num_mac
        pred_y['first_average_duration'] =pred_y['first_average_duration']+random.randint(-10,10)
        pred_y['multi_average_duration'] =pred_y['multi_average_duration']+random.randint(-10,10)
        pred_y['num_first_arrival'] =pred_y['num_first_arrival']*r #num_first_arrival
        pred_y['num_multi_arrival'] =pred_y['num_multi_arrival']*r #num_multi_arrival
        pred_y['average_duration'] =(pred_y['num_first_arrival']*pred_y['first_average_duration']+\
                                    pred_y['num_multi_arrival']+pred_y['multi_average_duration'])/\
                                    (pred_y['num_first_arrival']+pred_y['num_multi_arrival']) #average_duration
        pred_y['num_betw5_30Min'] =pred_y['num_betw5_30Min']*r #num_betw5_30Min
        pred_y['num_more30Min'] =pred_y['num_more30Min']*r #num_more30Min
        pred_y['num_less5Min'] =pred_y['num_less5Min']*r #num_less5Min
        return pred_y
    def get_inset_training_y(self,dates):
        sql_str = "select * from num_mac,average_duration,first_average_duration,multi_average_duration,\
                   num_first_arrival,num_multi_arrival,num_betw5_30Min,num_more30Min,num_less5Min \
                   from mbox_dailyreport2 where date in %s and store_id='%s'"%(dates,self.store_id)
        self.cur.execute(sql_str)
        training_y = self.cur.fetchall()
        training_y = np.array(training_y)
        if len(training_y) < 2 :
            """
            发邮件提醒:设备不可插值
            """
            training_y = None
        return training_y
    def get_history_avgAndmax(self,date):
        #获取一周均值，最大值
        sql_str = "select store_id,AVG(num_mac),MAX(num_mac) from mbox_dailyreport2 where \
                date>'%s' and date<'%s' and num_mac>0 group by store_id "%(date-datetime.timedelta(days=7),date)
        self.cur.execute(sql_str)
        data = self.cur.fetchall()
        data = np.array(data)
        #字典,key:店,values:均值,最值
        store_aveAndmax = dict(zip(data[:,0],data[:,1:]))
        return store_aveAndmax
    def get_today_data(self, date):
        sql_str = "select * from mbox_dailyreport2 where date='%s'"%date
        self.cur.execute(sql_str)
        today_data = self.cur.fetchall()
        return today_data


class MysqlAccesser(object):
    """
    连接数据库,获取数据
    属性:
        略
    方法:
        connect: 连接数据库
        load_raw_tra_data: 载入原始训练数据
        load_macs: 载入去黑去伪后的mac的列表
    """
    def __init__(self, store_id=None, start_t=None, end_t=None):
        #初始化数据库连接
        self.host1 = 'rdsiyj2ynqumiej.mysql.rds.aliyuncs.com'
        self.usr1 = 'rdcenter'
        self.pwd1 = 'RD123456789'
        self.db1 = 'mbox_web'
        self.conn1 = mdb.connect(self.host1, self.usr1, self.pwd1, self.db1)
        self.cur1 = self.conn1.cursor()
        self.cur1_1 = self.conn1.cursor(cursorclass=mdb.cursors.DictCursor)  # 带字典
        #初始化参数
        self.store_id = store_id
        self.start_t = start_t
        self.end_t = end_t
        self.days = 14
    def sql_close(self):
        self.conn1.commit()
        self.cur1.close()
        self.cur1_1.close()
        self.conn1.close()

    def load_raw_tra_data(self,valid_mbox_ids):
        table = 'tb_channel_mbox_template'
        sql_str = ("select * from %s where mbox_serial_num in %s and channel_id='%s' order by logdate"%
                  (table, tuple(valid_mbox_ids), self.store_id))
        self.cur1_1.execute(sql_str)
        raw_data=self.cur1_1.fetchall()
        return raw_data

    def load_macs(self,mbox_ids):
        #去除黑名单的mac列表
        sql_str = "select distinct a.macid from box_mac_ori_zb a where \
                    EXISTS (SELECT 1 FROM org_mac_brand o WHERE left(a.macid,6)=o.ieee )\
                    and not EXISTS (SELECT 1 FROM store_black_staff b WHERE a.macid=b.macid )\
                    and a.boxid in %s and logdate>='%s'and logdate<='%s' order by logdate"\
                    %(tuple(mbox_ids),self.start_t,self.end_t)
        self.cur1.execute(sql_str)
        raw_data=self.cur1.fetchall()
        macs = [i[0] for i in raw_data]
        return macs
    def load_raw_macs(self,mbox_ids):
        #没去除黑名单的mac列表
        sql_str = "select distinct a.macid from box_mac_ori_zb a where \
                    EXISTS (SELECT 1 FROM org_mac_brand o WHERE left(a.macid,6)=o.ieee )\
                    and a.boxid in %s and logdate>='%s'and logdate<='%s' order by logdate"\
                    %(tuple(mbox_ids),self.start_t,self.end_t)
        self.cur1.execute(sql_str)
        raw_data=self.cur1.fetchall()
        macs = [i[0] for i in raw_data]
        return macs
    def get_black_mac(self,macs):
        sql_str="SELECT type,count(1) from store_black_staff where  macid in %s GROUP BY type"%(tuple(mac_list),)
        self.cur1.execute(sql_str)
        black_data = self.cur1.fetchall()
        black_type = dict(black_data)
        return black_type#{'machine': 39L, 'staff': 350L}
    def get_macs_date_cnt(macs, mbox_ids, date):
        #每一个mac的出现日期和该天的采集量
        sql_str="SELECT macid,DATE_FORMAT(a.logdate,'%%Y-%%m-%%d'),count(DATE_FORMAT(a.logdate,'%%Y-%%m-%%d')) \
                from box_mac_ori_zb a WHERE a.macid in %s and a.boxid in %s and logdate>'%s' and logdate<'%s' \
                GROUP BY DATE_FORMAT(a.logdate,'%%Y-%%m-%%d') ,a.macid ORDER BY a.macid,a.logdate"\
                %(tuple(macs), tuple(mbox_ids),date-datetime.timedelta(days=14),date+datetime.timedelta(days=1))
        self.cur1.execute(sql_str)
        macs_data=cur.fetchall()# ('fcd73382d0ea', '2016-10-20', 613L)
        return macs_data


    def load_mac_data(self, mac,valid_mbox_ids):
        sql_str = "select * from box_mac_ori_zb a where macid='%s'and boxid in %s and logdate>='%s'and logdate<='%s' \
                   and EXISTS (SELECT 1 FROM org_mac_brand o WHERE left(macid,6)=o.ieee ) order by logdate"\
                   %(mac, tuple(valid_mbox_ids), self.start_t, self.end_t)

        self.cur1_1.execute(sql_str)
        raw_data=self.cur1_1.fetchall()
        return raw_data
    def get_raw_mboxs(self):
        sql_str = "select distinct mbox_serial_num from tb_channel_mbox_template where channel_id='%s'\
                order by mbox_serial_num"%(self.store_id)
        self.cur1.execute(sql_str)
        raw_data=self.cur1.fetchall()
        mbox_ids=[i[0] for i in raw_data]
        return mbox_ids

    def get_valid_mbox_inf(self,mbox_ids):
        valid_mbox_ids = []
        w = 0.4 # 表示每个盒子数量跟最大数量盒子占比关系
        sql_str = "select boxid,count(macid) num from box_mac_ori_zb a \
                    where boxid IN %s and EXISTS (SELECT 1 FROM org_mac_brand o WHERE left(macid,6)=o.ieee )\
                    and not EXISTS(SELECT 1 FROM  store_black_staff c WHERE a.macid=c.macid )\
                    and logdate>='%s'and logdate<='%s' GROUP BY boxid "%(tuple(mbox_ids),self.start_t,self.end_t)
        self.cur1_1.execute(sql_str)
        raw_data = self.cur1_1.fetchall()
        mbox_ids_num = {}.fromkeys(mbox_ids, 0)
        for i in raw_data:
            mbox_num_ids[i['boxid']] = i['num']
        try :
            num_max = max(mbox_num_ids.values())
            for boxid in mbox_num_ids:
                if (mbox_num_ids[boxid]*1.0/num_max>w \
                    or mbox_num_ids[boxid]>5000) \
                    and mbox_num_ids[boxid]>1000:
                    valid_mbox_ids.append(boxid)
        except :
            pass
        return valid_mbox_ids, mbox_ids_num
    def get_best_mbox(self,valid_mbox_ids):
        # 获得最佳的盒子信息:在线天数,盒子id,盒子index
        sql_str = "SELECT sum(mbox1 > 1000), sum(mbox2 > 1000), sum(mbox3 > 1000), sum(mbox4 > 1000) , mbox_id \
                FROM mbox_status a WHERE storeid=%s and date <='%s' order by -date limit %s"\
                %(self.store_id, self.start_t.date(),self.days)
        self.cur1.execute(sql_str)
        raw_data = self.cur1.fetchall()[0]
        mboxs_status = raw_data[:-1]#(Decimal('4'),Decimal('4'))盒子在线天数
        p = re.compile(r'\d+')
        mbox_ids = p.findall(raw_data[-1])#盒子id序列
        mbox_ids_tianshu = dict(zip(mbox_ids,mbox_status))
        for id in valid_mbox_ids :
            if id not in mbox_ids_tianshu:
                mbox_ids_tianshu.pop(id)
        best_tianshu = int(max(mbox_ids_tianshu.values))
        best_mboxid = max(mbox_ids_tianshu, key=mbox_ids_tianshu.get)
        best_index = mbox_ids[best_mboxid]+1
        return best_tianshu, best_index, best_mboxid

    def get_insert_tradata(self,best_index):
        # 插值训练数据
        sql_str = "SELECT mbox%s,date from mbox_status where date<='%s' and storeid='%s' and mbox%s>1000 order by \
                -date limit %s"%(best_index, self.end_t.date(), self.store_id, best_index, self.days)
        self.cur1.execute(sql_str)
        raw_data = cur.fetchall()
        raw_data = np.array(raw_data)
        #获取x
        data_x= np.array(raw_data[:,0],dtype=int)
        test_x, training_x = data_x[0],data_x[1:]
        #获取date
        training_dates = raw_data[1:,1] #数据类型str而不是datetime
        return test_x,training_x,training_dates
    def get_indoor_cnt(self,mac,mbox_ids):
        t1 = start_t.date()
        t2 = t1 - datetime.timedelta(days=90)
        sql_str = "SELECT * from box_mac_ori_zb where macid='%s' and boxid in %s and \
                  logdate>'%s'and logdate<'%s' limit 2"%(mac,tuple(mbox_ids),t2,t1)
        self.cur1.execute(sql_str)
        raw_data = cur.fetchall()
        return raw_data
    @classmethod
    def all_storeid(self):
        sql_str="SELECT distinct channel_id from tb_channel_mbox_template order by logdate"
        self.cur1.execute(sql_str)
        raw_data = self.cur1.fetchall()
        storeids = [i[0] for i in raw_data]
        return storeids
    def get_coef(self):
        sql_str="SELECT store_id,mac_coef from store_coefficient "
        self.cur1.execute(sql_str)
        data = self.cur1.fetchall()
        data = np.array(data)
        #字典,key:店,values:均值,最值
        store_macf = dict(zip(data[:,0],data[:,1:]))
        return store_macf









