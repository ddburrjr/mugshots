from datetime import datetime


def gen_stamp(date=datetime.now()):
    return f"{date:%Y%m%d.%s}"
