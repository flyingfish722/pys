import re
import pandas
import numpy as np
import datetime
from functions import *

data = pandas.Series([1,2,], index = [1,2,])

data2 = pandas.DataFrame([[1,2,3],[4,5,6],[4,5,6]])

d1 = str2date('30/4/2020')
d2 = str2date('1/5/2020')
print(d1 - d2)


