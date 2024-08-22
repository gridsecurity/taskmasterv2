from io import BytesIO
import base64
import pandas as pd
from datetime import datetime
from .conn import *


def create_splunk_log(m):
    today = datetime.today()
    dateMonth = today.strftime("%Y-%m")
    print(dateMonth)

    for f in m.attachments:
        fileObj = BytesIO(base64.b64decode(f.content))
        fileObj.seek(0)
        df = pd.read_csv(fileObj)
        df = df.fillna(0)
        
        if "Suspicious Failed Logon Attempts" in m.subject:
            rec = list(map(lambda x: {
                "site": x["site_name"],
                "dateMonth": dateMonth,
                "key": "suspiciousActivity",
                "source": "Suspicious Failed Logon Attempts",
                "count": int(x["attempts"]),
                "summary": "{} - {} - {} - {}".format(x["attempted_account"], x["host"], x["attempted_domains"], x["fail_reason"])
            }, df.to_records('dict')))
            db.splunk_logs.insert_many(rec)

        if "PAN General Alerts" in m.subject:
            rec = list(map(lambda x: {
                "site": x["site_name"],
                "dateMonth": dateMonth,
                "key": "suspiciousActivity",
                "source": "PAN General Alert",
                "count": 1,
                "summary": "{} - {} - {} - {}".format(x["dvc_name"], x["signature"], x["description"], x["_time"])
            }, df.to_records("dict")))
            db.splunk_logs.insert_many(rec)
            
        if "Account Added to Admin Group" in m.subject:
            rec = list(map(lambda x: {
                "site": x["Site"],
                "dateMonth": dateMonth,
                "key": "suspiciousActivity",
                "source": "Account Added to Admin group",
                "count": 1,
                "summary": "{} - {} - {} - {} - {}".format(x["Target_User"], x["Groups"], x["Source_User"], x["Host"], x["_time"])
            }, df.to_records('dict')))
            db.splunk_logs.insert_many(rec)