from django.db import models
from django.contrib import admin

# Create your models here.
"""
    本APP使用的数据表:
        mbox_collection: mbox采集量
        store_coefficient: 店的系数
        mbox_dailyreport_modifty: mbox修订版报表
        customer_mac:客流mbox
        store_blacklist:店黑名单
        macfilter:mac筛选
"""
class Mbox_Collection(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=4)
    date = models.DateField(verbose_name='日期')
    mbox1 = models.IntegerField(default=0)
    mbox2 = models.IntegerField(default=0)
    mbox3 = models.IntegerField(default=0)
    mbox4 = models.IntegerField(default=0)
    mbox_id = models.CharField(verbose_name='盒子编号列表',max_length=50)
    online_num = models.IntegerField(verbose_name='有效Mbox在线数量',default=0)
    class Meta:
        verbose_name = 'Mbox采集量'
        verbose_name_plural = 'Mbox采集量列表'
        db_table = 'mbox_collection'
        unique_together = ("date",'storeid')
class Mbox_CollectionAdmin(admin.ModelAdmin):
    list_display = ('storeid','date','mbox1','mbox2','mbox3','mbox4','mbox_id','online_num')
    search_fields = ('storeid','date','online_num',)
    list_filter = ('storeid','date',)
    ordering = ('-date',)
admin.site.register(Mbox_Collection,Mbox_CollectionAdmin)

class Macfilter(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=10)
    date = models.DateField(verbose_name='日期')
    num_raw_mac = models.IntegerField(verbose_name='原始mac数量',default=0)
    num_valid_mac = models.IntegerField(verbose_name='有效mac数量',default=0)
    num_staff = models.IntegerField(verbose_name='工作人员mac数量',default=0)
    num_machine = models.IntegerField(verbose_name='店内设备mac数量',default=0)
    num_customer = models.IntegerField(verbose_name='店内顾客mac数量',default=0)
    class Meta:
        verbose_name = 'Mac过滤'
        verbose_name_plural = 'Mac过滤列表'

        db_table = 'macfilter'
        unique_together = ("date",'storeid')
class MacfilterAdmin(admin.ModelAdmin):
    list_display=('storeid','date','num_raw_mac','num_valid_mac','num_staff','num_machine','num_customer')
    search_fields = ('storeid','date',)
    list_filter = ('storeid','date',)
    ordering = ('-date',)
admin.site.register(Macfilter,MacfilterAdmin)


class Addf(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=10)
    mac_coef = models.FloatField(default=1)
    cam_coef = models.FloatField(default=1)
    class Meta:
        verbose_name = 'store系数'
        verbose_name_plural = 'store系数列表'
        db_table = 'store_coefficient'
class AddfAdmin(admin.ModelAdmin):
    list_display = ('storeid','mac_coef','cam_coef')
    list_filter = ('storeid',)
    permissions = (
            ("inno", "inno2016"),
            )
admin.site.register(Addf,AddfAdmin)

class DailyReport_Modify(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=4)
    date = models.DateField(verbose_name='日期')
    cam_pc=models.IntegerField(verbose_name='摄像头批次',default=0)
    cam_rs=models.IntegerField(verbose_name='摄像头人次',default=0)
    store_pc = models.IntegerField(verbose_name='店批次',default=0)
    num_mac=models.IntegerField(verbose_name='Mac数量',default=0)
    average_duration=models.IntegerField(verbose_name='平均驻留时长',default=0)
    first_average_duration=models.IntegerField(verbose_name = '首次到店驻留时长',default=0)
    multi_average_duration=models.IntegerField(verbose_name = '多次到店驻留时长',default=0)
    num_first_arrival=models.IntegerField(verbose_name = '首次到店驻留人数',default=0)
    num_multi_arrival=models.IntegerField(verbose_name = '多次到店驻留人数',default=0)
    num_less5Min=models.IntegerField(verbose_name = '少于5分钟人数',default=0)
    num_more30Min=models.IntegerField(verbose_name = '大于30分钟人数',default=0)
    num_betw5_30Min=models.IntegerField(verbose_name = '5-30分钟人数',default=0)
    class Meta:
        verbose_name = 'Mbox修订版报表'
        verbose_name_plural = 'Mbox修订版列表'
        db_table = 'mbox_dailyreport_modifty'
        unique_together = ("date",'storeid')
class DailyReport_ModifyAdmin(admin.ModelAdmin):
    list_display=('storeid','date','cam_pc','cam_rs','num_mac','average_duration','first_average_duration','multi_average_duration',\
                  'num_first_arrival','num_multi_arrival','num_less5Min','num_more30Min','num_betw5_30Min')
    search_fields = ('storeid','date',)
    list_filter = ('storeid','date',)
    ordering = ('-date',)
    unique_together = ("date",'storeid')
admin.site.register(DailyReport_Modify,DailyReport_ModifyAdmin)

class customer_mac(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=10)
    date = models.DateField(verbose_name='日期')
    macid = models.CharField(verbose_name='店ID',max_length=12)
    arrival_type = models.IntegerField(verbose_name = '到店类型',default=0) # 1为首次2为多次
    staytime = models.IntegerField(verbose_name = '驻留时长',default=0)
    class Meta:
        verbose_name = '客流mac'
        verbose_name_plural = '客流mac列表'
        db_table = 'customer_mac'
        unique_together = ("date",'storeid','macid')
class Store_BlackList(models.Model):
    storeid = models.CharField(verbose_name='店ID',max_length=10)
    date = models.DateField(verbose_name='日期')
    macid = models.CharField(verbose_name='店ID',max_length=12)
    black_type = models.CharField(verbose_name='黑名单类型',max_length=10)
    class Meta:
        verbose_name = 'Mac黑名单'
        verbose_name_plural = 'Mac黑名单列表'
        db_table = 'store_blacklist'
        unique_together = ("date",'storeid','macid')

