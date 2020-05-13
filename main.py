import pandas
import sys
import warnings
from functions import *

warnings.filterwarnings('ignore')
encoding = 'utf8'
data_path = '../bb20200401-20200501.csv'

# 读取数据，检查日期周期
original_data = pandas.read_csv(data_path, encoding=encoding)
columns = ['data_date', 'platform', 'item_code', 'status',
           'list_date', 'inv', 'uv', 'pay_num', 'original_retail_price']
data = original_data[columns]

#print(data.isnull().any())
#sys.exit(0)

tmp = []
for each in data.data_date:
    tmp.append(str2date(each))
data['date'] = pandas.Series(tmp)
days = (data.iloc[-1].date - data.loc[0, 'date']).days - 29
if days < 0:
    print("数据周期不足30天")
    sys.exit(0)
else:
    begin_date = data.iloc[-1].date - datetime.timedelta(days=days)
    print("最新日期是：", data.loc[data.date == begin_date].iloc[0].data_date)

# 确定上架首日的新品
new_items = data.loc[(data.date >= begin_date) & (data.data_date == data.list_date)]
data.loc[new_items.index, 'heat'] = 0
data.loc[new_items.index, 'cer'] = 50
data.loc[new_items.index, 'xvnew'] = 1

for _ in range(days+1):
    tmp = begin_date + datetime.timedelta(days=_)
    data_this = data.loc[data.date == tmp]
    print("%s\n上新商品数为%d个" % (data_this.data_date.iloc[0], len(data_this.loc[data.xvnew == 1])))

    # 统计无效数据
    data_this.original_retail_price = data_this.original_retail_price.fillna(0)
    invalid_by_retail = (data_this.original_retail_price == 0)
    invalid_by_upi = ((data.uv == 0) & (data.pay_num ==0) & (data.inv == 0))
    print("吊牌价是0的商品个数有%d个，三零商品有%d个" % (list(invalid_by_retail).count(True),
                                       list(invalid_by_upi).count(True)))