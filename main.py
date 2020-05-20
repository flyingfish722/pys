import pandas
import sys
import json
import warnings
import datetime
import os
from score import *
import score
import time


def label():
    # pandas.options.display.max_rows = None  # 展开行
    warnings.filterwarnings('ignore')  # 忽略报警
    begin_time = time.time()
    p = os.path.join(os.path.dirname(sys.argv[0]), "configures", "global.json")
    with open(p) as f:
        global_config = json.load(f)
        encoding = global_config["encoding"]
        data_path = global_config["data_path"]

    # 读取数据，检查日期周期
    original_data = pandas.read_csv(data_path, encoding=encoding)
    columns = ['data_date', 'platform', 'item_code', 'status',
               'list_date', 'inv', 'uv', 'pv', 'pay_num',
               'atc_num', 'pay_amount', 'pay_retailamount',
               'original_retail_price']
    data = original_data[columns]
    if data[['data_date', 'platform', 'item_code', 'inv',
            'uv', 'pv', 'pay_num', 'atc_num', 'pay_amount',
            'pay_retailamount']].isnull().any().any():
        print("数据中存在空值，请检查后再试一次")
    data.original_retail_price = data.original_retail_price.fillna(0)
    data["date"] = data.data_date.apply(lambda x: str2date(x))
    idx_ld = data.list_date[data.list_date.isnull() == False].index
    data["list_date_date"] = data.list_date[idx_ld].apply(lambda x: str2date(x))

    # days = (data.iloc[-1].date - data.loc[0, 'date']).days - 29
    days = 0
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
    original_data["trans_rate"] = None
    original_data[ "an_rate"] = None
    original_data.loc[new_items.index, 'xvnew'] = 1
    original_data["inv_turn"] = None
    original_data["week_chain"] = None
    original_data["discount"] = None
    original_data["price"] = None
    data.loc[new_items.index, 'xvnew'] = 1
    idx_ld = data.list_date[data.list_date.isnull() == False].index
    td = data.loc[idx_ld, "date"] - data.loc[idx_ld, "list_date_date"]
    td_ = td.apply(lambda x: x.days)
    td_idx = td_[(td_ < 15) & (td_ > 0)].index
    original_data.loc[td_idx, "xvnew"] = td_[td_idx]

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
    end_time = time.time()
    print("时间段0：开始计算，用时", round(end_time-begin_time, 2), 's')
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
        platforms.append(pf_data)
    # tm_data = scoring_data.loc[(scoring_data.platform == 'TM') & (scoring_data.status == '出售中')]
    # jd_data = scoring_data.loc[(scoring_data.platform == 'JD') & (scoring_data.status == '上架')]

    # 计算热度
    print("开始计算热度")
    print('-' * 30)
    begin_time = time.time()
    calculate_heat(platforms, original_data, scoring_data, begin_date, days)
    print("热度计算完成")
    end_time = time.time()
    print("时间段%d：所有店铺热度计算完成，用时%.2fs" % (score.a, end_time-begin_time))
    begin_time = end_time
    score.a += 1
    print('-' * 30)

    # 计算热度
    print("开始计算效度")
    print('-' * 30)
    calculate_cer(platforms, original_data, scoring_data, begin_date, days)
    print("效度计算完成")
    end_time = time.time()
    print("时间段%d：所有店铺效度计算完成，用时%.2fs" % (score.a, end_time - begin_time))
    print('-' * 30)

    original_data.loc[data.date >= begin_date].to_csv(
        global_config["result_path"],
        encoding=global_config["encoding"],
        index=None)


if __name__ == "__main__":
    try:
        label()
    except Exception as e:
        print(e)
        print("程序出现错误，程序中止")
    finally:
        input("按任意键退出...")
