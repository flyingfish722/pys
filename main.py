import pandas
import sys
import warnings
from functions import *

warnings.filterwarnings('ignore')
encoding = 'utf8'
data_path = '../bb20200401-20200501.csv'
# k-means parameters
n_clusters = {
    'uv_relative': 4,
    'pv_relative': 4,
    'atc_num_relative': 4,
    'an_rate_relative': 4,
    'trans_rate_relative': 4,
}
# for k = 4
scores = [25, 50, 75, 100]
# score weights
score_weights = {
    'score_uv_relative': 0.23,
    'score_pv_relative': 0.23,
    'score_atc_num_relative': 0.22,
    'score_an_rate_relative': 0.1,
    'score_trans_rate_relative': 0.22,
}

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
for date_str in data.data_date:
    tmp.append(str2date(date_str))
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
platforms = []
tmp = list(set(scoring_data.platform))
for each_pf in tmp:
    idx = scoring_data.loc[(scoring_data.platform == each_pf)
                           & ((scoring_data.status == '出售中')
                              | (scoring_data.status == '上架'))].index
    pf_data = scoring_data.loc[idx]
    platforms.append((idx, pf_data))
# tm_data = scoring_data.loc[(scoring_data.platform == 'TM') & (scoring_data.status == '出售中')]
# jd_data = scoring_data.loc[(scoring_data.platform == 'JD') & (scoring_data.status == '上架')]


for pf_idx, platform in platforms:
    # 特征值（绝对值）
    idx = platform.loc[(platform.pv == 0) & (platform.date >= begin_date)].index
    platform.loc[idx, 'trans_rate'] = 0
    platform.loc[idx, 'an_rate'] = 0
    idx = platform.loc[(platform.pv != 0) & (platform.date >= begin_date)].index
    platform.loc[idx, 'an_rate'] = platform.loc[idx, 'atc_num'] / platform.loc[idx, 'pv']
    platform.loc[idx, 'trans_rate'] = platform.loc[idx, 'pay_num'] / platform.loc[idx, 'pv']
    idx = platform.loc[platform.an_rate > 1].index
    platform.loc[idx, 'an_rate'] = 1
    idx = platform.loc[platform.trans_rate > 1].index
    platform.loc[idx, 'trans_rate'] = 1

    # 特征值（相对）
    for _ in range(days + 1):
        tmp = begin_date + datetime.timedelta(days=_)
        idx = platform.loc[platform.date == tmp].index
        platform.loc[idx, 'uv_relative'] = platform.loc[idx, 'uv'] / platform.loc[idx, 'uv'].sum()
        platform.loc[idx, 'uv_relative'] = platform.loc[idx, 'uv_relative'].fillna(0)
        platform.loc[idx, 'pv_relative'] = platform.loc[idx, 'pv'] / platform.loc[idx, 'pv'].sum()
        platform.loc[idx, 'pv_relative'] = platform.loc[idx, 'pv_relative'].fillna(0)
        platform.loc[idx, 'atc_num_relative'] = platform.loc[idx, 'atc_num'] / platform.loc[idx, 'atc_num'].sum()
        platform.loc[idx, 'atc_num_relative'] = platform.loc[idx, 'atc_num_relative'].fillna(0)
        platform.loc[idx, 'an_rate_relative'] = platform.loc[idx, 'an_rate'] / platform.loc[idx, 'an_rate'].sum()
        platform.loc[idx, 'an_rate_relative'] = platform.loc[idx, 'an_rate_relative'].fillna(0)
        platform.loc[idx, 'trans_rate_relative'] = platform.loc[idx, 'trans_rate'] / platform.loc[idx, 'trans_rate'].sum()
        platform.loc[idx, 'trans_rate_relative'] = platform.loc[idx, 'trans_rate_relative'].fillna(0)

        # 对流量，访客，加购，加购率，转化率分别打分
        for column in ['uv_relative',
                       'pv_relative',
                       'atc_num_relative',
                       'an_rate_relative',
                       'trans_rate_relative',
                       ]:
            idx = platform.loc[(platform.date == tmp) & (platform[column] == 0)].index
            platform.loc[idx, 'score_'+column] = 0
            idx = platform.loc[(platform.date == tmp) & (platform[column] != 0)].index
            score_result = get_scores_of_best_kmeans_model(platform.loc[idx, column],
                                                           n_clusters[column],
                                                           scores)
            platform.loc[idx, 'score_'+column] = score_result
    idx = platform.loc[platform.date >= begin_date].index
    platform.loc[idx, 'heat_today'] = 0
    for score, weight in score_weights.items():
        platform.loc[idx, 'heat_today'] += platform.loc[idx, score] * weight


platforms[0][1].to_csv('../pf.csv', encoding='ansi')
# tm_data.to_csv('../tm.csv', encoding='ansi')




