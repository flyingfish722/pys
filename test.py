import re
import pandas
import datetime

data = pandas.Series([1,2,3.2342342,0,1,6], index = [2,3,4,5,6,7])

data2 = pandas.DataFrame([[1,2,3],[4,5,6],[4,5,6]])
print(data.sum())



