import pandas
import sys
import warnings
import datetime
from functions import *

pandas.options.display.max_rows = None
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
# n: weight
n_weights = {
    '1': 0.25,
    '7': 0.5,
    '30': 0.25,
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
print('-'*30)
# 确定上架首日的新品
new_items = data.loc[data.data_date == data.list_date]
original_data.loc[new_items.index, 'heat'] = 0
original_data.loc[new_items.index, 'cer'] = 50
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
    print('-' * 30)
# 打分池
scoring_data = data.loc[(data.xvnew != 1)
                        & (data.original_retail_price != 0)
                        & ((data.uv != 0) | (data.pay_num != 0) | (data.inv != 0))]
platforms = []
tmp = (set(scoring_data.platform))
for each_pf in tmp:
    pf_data = scoring_data.loc[(scoring_data.platform == each_pf)
                           & ((scoring_data.status == '出售中')
                              | (scoring_data.status == '上架'))]
    platforms.append( pf_data)
# tm_data = scoring_data.loc[(scoring_data.platform == 'TM') & (scoring_data.status == '出售中')]
# jd_data = scoring_data.loc[(scoring_data.platform == 'JD') & (scoring_data.status == '上架')]


for platform in platforms:
    print("平台：", platform.iloc[0]['platform'])
    # 特征值（绝对值）
    idx = platform.loc[platform.pv == 0].index
    platform.loc[idx, 'trans_rate'] = 0
    platform.loc[idx, 'an_rate'] = 0
    idx = platform.loc[platform.pv != 0].index
    platform.loc[idx, 'an_rate'] = platform.loc[idx, 'atc_num'] / platform.loc[idx, 'pv']
    platform.loc[idx, 'trans_rate'] = platform.loc[idx, 'pay_num'] / platform.loc[idx, 'pv']
    idx = platform.loc[platform.an_rate > 1].index
    platform.loc[idx, 'an_rate'] = 1
    idx = platform.loc[platform.trans_rate > 1].index
    platform.loc[idx, 'trans_rate'] = 1

    # 特征值（相对）
    for each_day in set(scoring_data.date):
        idx = platform.loc[platform.date == each_day].index
        for cl in ['uv', 'pv', 'atc_num', 'an_rate', 'trans_rate']:
            platform.loc[idx, cl+'_relative_1'] = platform.loc[idx, cl] / platform.loc[idx, cl].sum()
            platform.loc[idx, cl+'_relative_1'] = platform.loc[idx, cl+'_relative_1'].fillna(0)

    idx = platform.loc[platform.date >= begin_date].index
    for n in n_weights.keys():
        # 计算出当天的_7 _30
        if n != '1':
            n_days = int(n)
            for i in idx:
                today_date = platform.loc[i, 'date']
                if platform.loc[i, 'list_date']:
                    list_date = str2date(platform.loc[i, 'list_date'])
                    interval = (today_date - list_date).days + 1
                    if 0 < interval < n_days:
                        origin = list_date
                    else:
                        origin = today_date - datetime.timedelta(n_days - 1)
                        interval = n_days
                else:
                    origin = today_date - datetime.timedelta(n_days - 1)
                    interval = n_days
                n_days_data = platform.loc[(origin <= platform.date)
                                           & (platform.date <= today_date)
                                           & (platform.item_code == platform.loc[i, 'item_code'])]
                for cl in ['uv', 'pv', 'atc_num', 'an_rate', 'trans_rate']:
                    tmp = cl+'_relative_'
                    platform.loc[i, tmp+n] = n_days_data[tmp+str(1)].sum()/interval * n_days
                print("\r处理完%d的_%s相对特征" % (i, n), end='', flush=True)
            print()
    print()
            # platform.to_csv('../tm.csv', encoding='ansi')
            # sys.exit(0)
    for _ in range(days + 1):
        today_date = begin_date + datetime.timedelta(days=_)
        print(today_date, ": ")
        # 分别对不同n的属性打分
        for n in n_weights.keys():
            print("对_%s特征进行打分" % n)
            for cl, k in n_clusters.items():
                tmp = cl+'_'+n
                idx = platform.loc[(platform.date == today_date) & (platform[tmp] == 0)].index
                platform.loc[idx, 'score_'+tmp] = 0
                idx = platform.loc[(platform.date == today_date) & (platform[tmp] != 0)].index
                try:
                    score_result = get_scores_of_best_kmeans_model(platform.loc[idx, tmp],
                                                                   k,
                                                                   scores)
                except ValueError:
                    print(tmp)
                    platform.to_csv('../exception.csv', encoding='ansi')
                    sys.exit(0)
                platform.loc[idx, 'score_'+tmp] = score_result
        print()
    idx = platform.loc[platform.date >= begin_date].index
    platform.loc[idx, 'heat'] = 0
    for n, n_weight in n_weights.items():
        platform.loc[idx, 'heat_'+n] = 0
        # 根据特征计算heat_n
        print("计算heat_"+n)
        for score, score_weight in score_weights.items():
            platform.loc[idx, 'heat_'+n] += platform.loc[idx, score+'_'+n] * score_weight
        # 计算最终heat
        platform.loc[idx, 'heat'] += platform.loc[idx, 'heat_'+n] * n_weight
    print("计算heat")
    original_data.loc[platform.index, 'heat'] = platform.heat
    print('-' * 30)

original_data.to_csv('../label.csv', encoding='ansi')
# tm_data.to_csv('../tm.csv', encoding='ansi')




