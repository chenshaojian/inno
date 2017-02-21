# -*-coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from ips_core.mysql_raw import MysqlAccesserRepoert,MysqlAccesser
from reports.report import BlackList,InnoReport,InnoIps
import json
from multiprocessing import Pool
'''
    api接口说明:
        training_result: 室内定位训练接口,用于训练精度的测试，训练精度需高达80%合理
        ips_data: 对采集的数据进行分析，采用的算法为knn算法
        allstore_ips: 计算所有店铺的数据_
        allstore_black: 计算所有店铺的黑名单
        insert_data: 数据插值
'''
# Create your views here.

@csrf_exempt
def home(request):
    return render(request,'wifi.html')

@csrf_exempt
def training_result(request):
    '''
    请求方式:Get
    参数:
        keys: 训练的店铺id
        训练的mac id
        训练的开始时间
        训练的结束时间
        训练的区域:0为店内,1为店外
        返回结果: 训练精度
    '''

    store_id = str(request.GET.get('store_id'))
    training_mac = str(request.GET.get('mac'))
    start_t = str(request.GET.get('stime'))
    start_t = start_t.replace('T',' ')
    start_t=datetime.datetime.strptime(start_t,"%Y-%m-%d %H:%M")
    end_t = str(request.GET.get('etime'))
    end_t = end_t.replace('T',' ')
    end_t=datetime.datetime.strptime(end_t,"%Y-%m-%d %H:%M")
    area=int(request.GET.get('area'))

    sqlacs = MysqlAccesser(start_t, end_t, store_id)
    model = TrainingModel(sqlacs)
    p = model.training_result(area, training_mac)
    data={}
    data['p']=round(p, 1)
    return HttpResponse(json.dumps(data))





@csrf_exempt
def ips_data(request):
    '''
    请求方式: Get
    参数说明:
        店铺id
        日期,计算的时间段为8:30-18:30
    返回结果: 需要post的数据

    '''
    #1.获取日期,店id
    #2.获取店的训练数据
    #3.获取店的mac列表
    #4.有效的mac测试数据
    store_id = str(request.GET.get('store_id'))
    date = request.GET.get('date')
    sqlacs = MysqlAccesser(start_t, end_t, store_id)
    sqlacs_local = MysqlAccesserRepoert(start_t, end_t, store_id)
    if date is None:
        date = datetime.datetime.now().date()
    else:
        date = datetime.datetime.strptime(date,"%Y-%m-%d").date()
    start_t = '%s 08:30:00' % date
    end_t = '%s 18:30:00' % date
    start_t = datetime.datetime.strptime(start_t,"%Y-%m-%d %H:%M:%S")
    end_t = datetime.datetime.strptime(end_t,"%Y-%m-%d %H:%M:%S")
    '''
    室内定位
    '''
    rpt_model = InnoReport(store_id, date, sqlacs, sqlacs_local)
    valid_mbox_ids, mbox_ids_num = rpt_model.get_valid_mbox_inf()
    post_data = {'store_id':self.store_id,'date':str(date())}
    if len(valid_mbox_ids) == 0:
        post_data = {'average_duration':0,'num_mac':0,'multi_average_duration':0,'first_average_duration':0 ,
                'store_id':self.store_id,'date':str(date()),'num_first_arrival':0,'num_multi_arrival':0,
                'num_less5Min':0,'num_more30Min':0,'num_betw5_30Min':0}
    elif len(valid_mbox_ids) < 3:
        #r = requests.post('http://127.0.0.1:8000/test/',{'a':13})
        #r = requests.post('http://112.74.76.94:8000/api/mac_data/', post_dict)
        #post_data = r.text
        post_data = rpt_model.insert_mac_data(valid_mbox_ids)
    else :
        store_mac_time,num_valid_mac = rpt_model.ips_calculate(valid_mbox_ids)
        post_data = self.output_data(store_mac_time)
    '''
    日报制作
    '''

    num_customer = post_data['num_mac']
    rpt_model.mbox_coll_num_rpt(mbox_ids_num,valid_mbox_ids)
    rpt_model.macfilter_rpt(num_valid_mac,num_customer,mbox_ids)

    return HttpResponse(store_id)

@csrf_exempt
def blacklist(request):
    '''
    请求方式: Get
    参数说明:
        日期
    返回结果
    '''
    sqlacs = MysqlAccesser()
    b = BlackList(sqlacs)
    no_cal = b.blacklist()
    return HttpResponse(no_cal)

def link(store_id,date):
    r = requests.get('http://127.0.0.1:8001/ips/',params={'shop_id':self.shop_id,'date':self.date},timeout=84000)
    return store_id
@csrf_exempt
def allstore_ips(request):
    '''
    请求方式: Get
    参数说明:
        date: 日期
    返回结果
    '''

    date = request.GET.get('date')
    sqlacs = MysqlAccesser()
    all_storeid = sqlacs.all_storeid()
    p = Pool(8)
    result = []
    for store_id in all_storeid:
        result.append(p.apply_async(link,(store_id,date)))
    p.close()
    p.join()
    cal_storeid = [i.get() for i in result]
    return HttpResponse('ok')


@csrf_exempt
def insert_data(request):
    '''
    请求方式: Get
    参数说明:
        店铺id
        日期
    返回结果:插值的数据
    '''
    if request.method == 'POST':
        store_id = request.POST.get('store_id',0)
        date = request.POST.get('date',0)
        valid_mbox_ids = request.POST.get('valid_mbox_ids',0)
    elif request.method == 'GET':
        store_id = str(request.GET.get('store_id'))
        date = request.GET.get('date')
        valid_mbox_ids = request.GET.get('valid_mbox_ids')
    if date is None:
        date = datetime.datetime.now().date()
    else:
        date = datetime.datetime.strptime(date,"%Y-%m-%d").date()
    start_t = '%s 08:30:00' % date
    end_t = '%s 18:30:00' % date
    start_t = datetime.datetime.strptime(start_t,"%Y-%m-%d %H:%M:%S")
    end_t = datetime.datetime.strptime(end_t,"%Y-%m-%d %H:%M:%S")
    sqlacs = MysqlAccesser(start_t, end_t, store_id)
    sqlacs_local = MysqlAccesserRepoert(start_t, end_t, store_id)
    ips_model = InnoIps(store_id,date,sqlacs,sqlacs_local)
    post_data = ips_model.insert_mac_data(valid_mbox_ids)
    return HttpResponse(post_data)














