import json
import main
import pandas
import random


def boom(fp, eco):
    data = pandas.read_csv(fp, encoding=eco)
    idx = data.heat[data.heat >= 40].index
    data.loc[idx, "heat"] = data.loc[idx, "heat"] * (1 - random.random()*0.003)
    idx = data.heat[data.heat < 40].index
    data.loc[idx, "heat"] = data.loc[idx, "heat"] * (1 + random.random()*0.005)
    idx = data.cer[(data.xvnew >=2) & (data.xvnew <= 15) & (data.cer >= 40)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 + random.random() * 0.005)
    idx = data.cer[(data.xvnew >=2) & (data.xvnew <= 15) & (data.cer < 40)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 - random.random() * 0.003)
    idx = data.cer[(data.xvnew.isnull()) & (data.cer >= 90)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 - random.random() * 0.003)
    idx = data.cer[(data.xvnew.isnull()) & (data.cer >= 40) & (data.cer < 90)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 + random.random() * 0.005)
    idx = data.cer[(data.xvnew.isnull()) & (data.cer >= 30) & (data.cer < 40)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 - random.random() * 0.003)
    idx = data.cer[(data.xvnew.isnull()) & (data.cer < 30)].index
    data.loc[idx, "cer"] = data.loc[idx, "cer"] * (1 - random.random() * 0.005)

    idx = data.heat[data.xvnew == 1].index
    data.loc[idx, "heat"] = 0
    data.loc[idx, "cer"] = 50

    data.to_csv(fp, encoding=eco, index=None)

global_config = {
    "encoding": "utf8",
    "data_path": "../data/bb.csv",
    "result_path": "../result/bblabel.csv"
}
heat_config = {
  # k-means算法在不同字段的分类数K的取值
  "n_clusters": {
    "uv_relative": 4,
    "pv_relative": 4,
    "atc_num_relative": 4,
    "an_rate_relative": 4,
    "trans_rate_relative": 4
  },

  # "or k = 4,
  "scores": [25, 50, 75, 100],

  # 计算cer_n时，不同字段得分的权重
  "score_weights": {
      "score_uv_relative": 0.23,
      "score_pv_relative": 0.23,
      "score_atc_num_relative": 0.22,
      "score_an_rate_relative": 0.1,
      "score_trans_rate_relative": 0.22
  },

  # 计算cer时，不同周期的权重
  "n_weights": {
      "1": 0.25,
      "7": 0.5,
      "30": 0.25
  }
}
cer_config = {
  # k-means算法在不同字段的分类数K的取值
  "n_clusters": {
    "pay_num_relative": 5,
    "pay_amount_relative": 5,
    "inv": 4,
    "inv_turn": 4,
    "week_chain": 4,
    "discount": 4,
    "price": 4
  },

  # k-means中不同k值的打分
  "scores": {
    "4": [25, 50, 75, 100],
    "5": [20, 40, 60, 80, 100]
  },

  # 计算cer_n时，不同字段得分的权重
  "score_weights":{
      "score_pay_num_relative": 0.21,
      "score_pay_amount_relative": 0.21,
      "score_inv": 0.14,
      "score_inv_turn": 0.1,
      "score_week_chain": 0.13,
      "score_discount": 0.15,
      "score_price": 0.06
  },

  # 计算cer时，不同周期的权重
  "n_weights": {
      "1": 0.25,
      "7": 0.5,
      "30": 0.25
  }
}
"""以上是可调整的参数"""

for config_path, config in {"configures/global.json": global_config,
                            "configures/heat.json": heat_config,
                            "configures/cer.json": cer_config}.items():
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

# main.label()
boom(global_config["result_path"],
     global_config["encoding"])


