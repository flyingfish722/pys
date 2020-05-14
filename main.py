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
           'list_date', 'inv', 'uv', 'pv', 'pay_num',
           'atc_num',
           'original_retail_price']
data = original_data[columns]
data.original_retail_price = data.original_retail_price.fillna(0)
# print(data.isnull().any())
# sys.exit(0)

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
    invalid_by_retail = (data_this.original_retail_price == 0)
    invalid_by_upi = ((data_this.uv == 0) & (data_this.pay_num == 0) & (data_this.inv == 0))
    print("吊牌价是0的商品个数有%d个，三零商品有%d个" % (list(invalid_by_retail).count(True),
                                       list(invalid_by_upi).count(True)))

# 打分池
scoring_data = data.loc[(((data.xvnew == 1)
                          | (data.original_retail_price == 0)
                          | ((data.uv == 0) & (data.pay_num == 0) & (data.inv == 0)))
                         & (data.date >= begin_date)) == False]

tm_data = scoring_data.loc[(scoring_data.platform == 'TM') & (scoring_data.status == '出售中')]
jd_data = scoring_data.loc[(scoring_data.platform == 'JD') & (scoring_data.status == '上架')]


for each in [tm_data, jd_data]:
    # 特征值（绝对值）
    idx = each.loc[(each.pv == 0) & (each.date >= begin_date) & (each.atc_num == 0)].index
    each.loc[idx, 'atc_rate'] = 0
    idx = each.loc[(each.pv == 0) & (each.date >= begin_date) & (each.atc_num != 0)].index
    each.loc[idx, 'atc_rate'] = 1
    idx = each.loc[(each.pv == 0) & (each.date >= begin_date)].index
    each.loc[idx, 'conv_rate'] = 0
    idx = each.loc[(each.pv != 0) & (each.date >= begin_date)].index
    each.loc[idx, 'atc_rate'] = each.loc[idx, 'atc_num'] / each.loc[idx, 'pv']
    each.loc[idx, 'conv_rate'] = each.loc[idx, 'pay_num'] / each.loc[idx, 'pv']
    idx = each.loc[each.atc_rate > 1].index
    each.loc[idx, 'atc_rate'] = 1
    idx = each.loc[each.conv_rate > 1].index
    each.loc[idx, 'conv_rate'] = 1

    # 特征值（相对）
    for _ in range(days + 1):
        tmp = begin_date + datetime.timedelta(days=_)
        idx = each.loc[each.date == tmp].index
        each.loc[idx, 'uv_relative'] = each.loc[idx, 'uv'] / each.loc[idx, 'uv'].sum()
        each.loc[idx, 'uv_relative'] = each.loc[idx, 'uv_relative'].fillna(0)
        each.loc[idx, 'pv_relative'] = each.loc[idx, 'pv'] / each.loc[idx, 'pv'].sum()
        each.loc[idx, 'pv_relative'] = each.loc[idx, 'pv_relative'].fillna(0)
        each.loc[idx, 'atc_num_relative'] = each.loc[idx, 'atc_num'] / each.loc[idx, 'atc_num'].sum()
        each.loc[idx, 'atc_num_relative'] = each.loc[idx, 'atc_num_relative'].fillna(0)
        each.loc[idx, 'atc_rate_relative'] = each.loc[idx, 'atc_rate'] / each.loc[idx, 'atc_rate'].sum()
        each.loc[idx, 'atc_rate_relative'] = each.loc[idx, 'atc_rate_relative'].fillna(0)
        each.loc[idx, 'conv_rate_relative'] = each.loc[idx, 'conv_rate'] / each.loc[idx, 'conv_rate'].sum()
        each.loc[idx, 'conv_rate_relative'] = each.loc[idx, 'conv_rate_relative'].fillna(0)

    # 相对特征值为0的打分
    for _ in ['uv_relative',
              'pv_relative',
              'atc_num_relative',
              'atc_rate_relative',
              'conv_rate_relative',
              ]:
        idx = each.loc[(each.date >= begin_date) & (each[_] == 0)].index
        each.loc[idx, _+'_score'] = 0

tm_data.to_csv('../tm.csv', encoding='ansi')




