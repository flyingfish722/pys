import pandas
import datetime
import sys
import re

encoding = 'utf8'
data_path = '../bb20200401-20200501.csv'

# 读取
data = pandas.read_csv(data_path, encoding=encoding)
ptn = r'(\d+)/(\d+)/(\d+)'
d = []
for each in data.data_date:
    s = re.search(ptn, each)
    d.append(datetime.date(int(s.group(3)), int(s.group(2)), int(s.group(1))))
data['date'] = pandas.Series(d)
if (data.iloc[-1].date - data.loc[0, 'date']).days < 30:
    print("数据周期不足30天")
    sys.exit(0)
else:
    print("最新日期是：", data.iloc[-1].data_date)
