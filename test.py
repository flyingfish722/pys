import re
import pandas
import datetime

data = pandas.Series([1,2,3,4,5,6], index = ['a',3,4,5,6,7])

data2 = pandas.DataFrame([[1,2,3],[4,5,6],[4,5,6]])
l = [False, True, True]
print(data2)
d = data2.loc[data2[2] == 6]
d.iloc[0,0] = 0
print(d)
print(data2)