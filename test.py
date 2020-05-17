import re
import pandas
import numpy as np
import datetime
import json
import sys

from functions import *

data = pandas.Series([1,2,], index = [1,2,])

data2 = pandas.DataFrame([[1,2,3],[4,5,6],[4,5,6]], columns=["a", "b", "c"])
data3 = pandas.DataFrame([[40,50,60],[40,50,60]], columns=["a", "b", "c"])

data2.loc[[0, 1], ["a"]] = data3["b"]
print(data2[["a"]])

# original_data = pandas.read_csv("../bb20200401-20200501.csv", encoding='utf8')
# platform = pandas.read_csv("../123.csv", encoding='ansi', index_col=0)
# print(platform[["cer", "inv_turn_1", "week_chain_1", "discount_1", "price_1"]])
#
#
# print(platform.index[0])
# original_data["cer"] = None
# original_data["inv_turn"] = None
# original_data["week_chain"] = None
# original_data["discount"] = None
# original_data["price"] = None
# original_data.loc[platform.index, ["cer", "inv_turn", "week_chain", "discount", "price"]] = \
#     platform[["cer", "inv_turn_1", "week_chain_1", "discount_1", "price_1"]]
# print(original_data.loc[platform.index, ["cer", "inv_turn", "week_chain", "discount", "price"]])
# #original_data.to_csv("../1234.csv", encoding='ansi', index=None)
