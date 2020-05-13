import re
import datetime


def str2date(s):
    # transform date from str to datetime.date
    ptn = r'(\d+)/(\d+)/(\d+)'
    m = re.search(ptn, s)
    return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))