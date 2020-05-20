import tkinter
from tkinter import filedialog
from main import label
import os
import sys
import json

root = tkinter.Tk()
root.withdraw()
data_path = filedialog.askopenfilename(
                        parent=root,
                        initialdir="../data/",
                        title='select input data',
                        filetypes=[("csv file", ".csv")])
root_dir = os.path.split(os.path.dirname(sys.argv[0]))[0]
p = os.path.join(os.path.dirname(sys.argv[0]), "configures", "global.json")
global_config = {
    "encoding": "utf8",
    "root_dir": root_dir,
    "data_path": data_path
}
with open(p, "w") as f:
    json.dump(global_config, f, indent=4)
sys.exit(0)
try:
    label()
except Exception as e:
    print(e)
    print("程序出现错误，程序中止")
finally:
    input("按任意键退出...")
