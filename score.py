from functions import *
import json
import sys
import time
import os
a = 1


def calculate_heat(platforms, original_data, scoring_data, begin_date, days, root_dir):
    global a

    with open(os.path.join(root_dir,"configures","heat.json"), encoding='utf') as f:
        config_heat = json.load(f)
        n_clusters = config_heat['n_clusters']
        scores = config_heat['scores']
        score_weights = config_heat['score_weights']
        n_weights = config_heat['n_weights']
    for platform in platforms:
        begin_time = time.time()
        p_begin_time = begin_time
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
                platform.loc[idx, cl + '_relative_1'] = platform.loc[idx, cl] / platform.loc[idx, cl].sum()
                platform.loc[idx, cl + '_relative_1'] = platform.loc[idx, cl + '_relative_1'].fillna(0)

        idx = platform.loc[platform.date >= begin_date].index
        for n in n_weights.keys():
            # 计算出当天的_7 _30
            if n != '1':
                n_days = int(n)
                for i in idx:
                    n_days_data, interval = get_n_days_data_for_one_item(platform, n_days, i)
                    for cl in ['uv', 'pv', 'atc_num', 'an_rate', 'trans_rate']:
                        tmp = cl + '_relative_'
                        platform.loc[i, tmp + n] = n_days_data[tmp + str(1)].sum() / interval * n_days
                    print("\r计算index:%d的_%s相对特征" % (i, n), end='', flush=True)
                print()
                end_time = time.time()
                print("时间段%d：计算index:%d的_%s相对特征，用时%.2fs" % (a, i, n, end_time-begin_time))
                a += 1
                begin_time = end_time
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
                    tmp = cl + '_' + n
                    idx = platform.loc[(platform.date == today_date) & (platform[tmp] == 0)].index
                    platform.loc[idx, 'score_' + tmp] = 0
                    idx = platform.loc[(platform.date == today_date) & (platform[tmp] != 0)].index
                    if len(idx) >= 10:
                        score_result = get_scores_of_best_kmeans_model(platform.loc[idx, tmp],
                                                                       k,
                                                                       scores)
                        platform.loc[idx, 'score_' + tmp] = score_result
                    else:
                        print(tmp, "非零样本数小于10")
                        platform.loc[idx, 'score_' + tmp] = 100

            print()
        idx = platform.loc[platform.date >= begin_date].index
        platform.loc[idx, 'heat'] = 0
        for n, n_weight in n_weights.items():
            platform.loc[idx, 'heat_' + n] = 0
            # 根据特征计算heat_n
            print("计算heat_" + n)
            for score, score_weight in score_weights.items():
                platform.loc[idx, 'heat_' + n] += platform.loc[idx, score + '_' + n] * score_weight
            # 计算最终heat
            platform.loc[idx, 'heat'] += platform.loc[idx, 'heat_' + n] * n_weight
        print("计算heat")
        end_time = time.time()
        print("时间段%d：计算heat，用时%.2fs" % (a, end_time - begin_time))
        a += 1
        original_data.loc[platform.index, ["heat", "trans_rate", "an_rate"]] = \
            platform[["heat", "trans_rate", "an_rate"]]
        end_time = time.time()
        print("时间段%d：%s店铺热度计算完成，用时%.2fs" % (a, platform.platform.iloc[0], end_time - p_begin_time))
        a += 1
        print('-' * 30)


def calculate_cer(platforms, original_data, scoring_data, begin_date, days, root_dir):
    global a

    with open(os.path.join(root_dir,"configures","cer.json"), encoding='utf') as f:
        config_heat = json.load(f)
        n_clusters = config_heat['n_clusters']
        scores = config_heat['scores']
        score_weights = config_heat['score_weights']
        n_weights = config_heat['n_weights']

    for platform in platforms:
        begin_time = time.time()
        p_begin_time = begin_time
        print("平台：", platform.iloc[0]['platform'])
        # 特征值（绝对值）


        # 特征值（相对）
        for each_day in set(scoring_data.date):
            idx = platform.loc[platform.date == each_day].index
            for cl in ['pay_num', 'pay_amount']:
                platform.loc[idx, cl + '_relative_1'] = platform.loc[idx, cl] / platform.loc[idx, cl].sum()
                platform.loc[idx, cl + '_relative_1'] = platform.loc[idx, cl + '_relative_1'].fillna(0)

        idx = platform.loc[platform.date >= begin_date].index
        for n in n_weights.keys():
            # 计算出当天的_7 _30
            if n == '1':
                platform.loc[idx, "discount_1"] = platform.pay_amount[idx] / \
                                                platform.pay_retailamount[idx]
                platform.loc[idx, "discount_1"] = platform.loc[idx, "discount_1"].fillna(1)
                idx_ = platform.loc[platform.discount_1 > 1].index
                platform.loc[idx_, "discount_1"] = 1

                platform.loc[idx, "price_1"] = platform.pay_amount[idx] / \
                                             platform.pay_num[idx]
                platform.loc[idx, "price_1"] = platform.loc[idx, "price_1"].fillna(0)
                platform["inv_1"] = platform["inv"]

                for i in idx:
                    n14_days_data, n14_interval = get_n_days_data_for_one_item(platform, 14, i)
                    pay_num_n14 = n14_days_data.pay_num.sum() / n14_interval * 14
                    if pay_num_n14 == 0:
                        platform.loc[i, "inv_turn_1"] = n14_days_data.loc[i, "inv"]
                    else:
                        platform.loc[i, "inv_turn_1"] = \
                            n14_days_data.loc[i, "inv"] / (pay_num_n14 / 2)
                    if n14_interval < 14:
                        platform.loc[i, "week_chain_1"] = -1
                    else:
                        n7_days_data, n7_interval = get_n_days_data_for_one_item(platform, 7, i)
                        pay_num_n8_14 = n14_days_data.pay_num.sum() - n7_days_data.pay_num.sum()
                        if pay_num_n8_14 == 0:
                            platform.loc[i, "week_chain_1"] = n7_days_data.pay_num.sum()
                        else:
                            platform.loc[i, "week_chain_1"] = \
                                n7_days_data.pay_num.sum() / \
                                (n14_days_data.pay_num.sum() - n7_days_data.pay_num.sum() + 1)
                    print("\r计算index: %d的周转，周环比" % i, end="", flush=True)
                print()
                end_time = time.time()
                print("时间段%d：计算index: %d的周转，周环比，用时%.2fs" % (a, i, end_time - begin_time))
                begin_time = end_time
                a += 1
            else:
                n_days = int(n)
                for i in idx:
                    n_days_data, interval = get_n_days_data_for_one_item(platform, n_days, i)
                    for cl in ['pay_num', 'pay_amount']:
                        tmp = cl + '_relative_'
                        platform.loc[i, tmp + n] = n_days_data[tmp + str(1)].sum() / interval * n_days
                    for cl, numerator, denominator in [
                        ("discount", "pay_amount", "pay_retailamount"),
                        ("price", "pay_amount", "pay_num")
                    ]:
                        tmp = cl + '_' + n
                        platform.loc[i, tmp] = n_days_data[numerator].sum() /\
                                               n_days_data[denominator].sum()
                    print("\r计算index: %d的_%s特征" % (i, n), end="", flush=True)
                print()
                end_time = time.time()
                print("时间段%d：计算index: %d的%s特征，用时%.2fs" % (a, i, n, end_time - begin_time))
                begin_time = end_time
                a += 1
                tmp = "discount" + '_' + n
                platform.loc[idx, tmp] = platform.loc[idx, tmp].fillna(1)
                idx_ = platform.loc[platform[tmp] > 1].index
                platform.loc[idx_, tmp] = 1
                tmp = "price" + '_' + n
                platform.loc[idx, tmp] = platform.loc[idx, tmp].fillna(0)

        # platform.to_csv('../tm.csv', encoding='ansi')
        # sys.exit(0)
        for _ in range(days + 1):
            today_date = begin_date + datetime.timedelta(days=_)
            print(today_date, ": ")
            today_idx = platform.loc[platform.date == today_date].index
            # 分别对不同n的属性打分
            ignore_inv_turn = False
            for n in n_weights.keys():
                print("对_%s特征进行打分" % n)
                for cl, k in n_clusters.items():
                    tmp = cl + '_' + n
                    if n != '1' and cl in ["inv_turn", "week_chain", "inv"]:
                        platform.loc[today_idx, 'score_' + tmp] = platform.loc[today_idx, "score_"+cl+"_1"]
                        continue
                    if n == '1' and cl == "inv_turn" and ignore_inv_turn:
                        continue
                    if cl == "discount" and \
                            (platform.loc[today_idx, tmp].max() - platform.loc[today_idx, tmp].min()) < 0.15:
                        platform.loc[today_idx, 'score_' + tmp] = 100
                        continue
                    if cl == 'inv' and \
                            platform.loc[today_idx, tmp].max() < (platform.loc[today_idx, tmp].min()*5):
                        platform.loc[today_idx, 'score_'+tmp] = 100
                        platform.loc[today_idx, "score_inv_turn_"+n] = 100
                        ignore_inv_turn = True
                        continue
                    if cl == "week_chain":
                        idx = platform.loc[(platform.date == today_date) & (platform[tmp] == -1)].index
                        platform.loc[idx, 'score_' + tmp] = 0
                        idx = platform.loc[(platform.date == today_date) & (platform[tmp] != -1)].index
                    else:
                        idx = platform.loc[(platform.date == today_date) & (platform[tmp] == 0)].index
                        platform.loc[idx, 'score_' + tmp] = 0
                        idx = platform.loc[(platform.date == today_date) & (platform[tmp] != 0)].index

                    if len(idx) >= 10:
                        try:
                            score_result = get_scores_of_best_kmeans_model(platform.loc[idx, tmp],
                                                                           k,
                                                                           scores[str(k)])
                        except ValueError:
                            print(tmp, "中包含空值")
                            platform.to_csv('../exception.csv', encoding='ansi')
                            sys.exit(0)
                        platform.loc[idx, 'score_' + tmp] = score_result
                    else:
                        print(tmp, "非零样本数小于10")
                        platform.loc[idx, 'score_' + tmp] = 100
            print()
        idx = platform.loc[platform.date >= begin_date].index
        platform.loc[idx, 'cer'] = 0
        for n, n_weight in n_weights.items():
            platform.loc[idx, 'cer_' + n] = 0
            # 根据特征计算cer_n
            print("计算cer_" + n)
            for score, score_weight in score_weights.items():
                platform.loc[idx, 'cer_' + n] += platform.loc[idx, score + '_' + n] * score_weight
            # 计算最终cer
            platform.loc[idx, 'cer'] += platform.loc[idx, 'cer_' + n] * n_weight
        print("计算cer")
        end_time = time.time()
        print("时间段%d：计算cer，用时%.2fs" % (a, end_time - begin_time))
        begin_time = end_time
        a += 1
        for _ in ["cer", "inv_turn", "week_chain", "discount", "price"]:
            if _ == "cer":
                original_data.loc[platform.index, _] = \
                    platform[_]
            else:
                original_data.loc[platform.index, _] = \
                    platform[_+"_1"]
        end_time = time.time()
        print("时间段%d：%s店铺效度计算完成，用时%.2fs" % (a, platform.platform.iloc[0], end_time - p_begin_time))
        a += 1
        print('-' * 30)