from bson.objectid import ObjectId
import pandas as pd
from datetime import datetime
from dateutil.parser import parse
from .conn import *
import pymongo

def procMessage(m):
    # get users
    list = []
    ignoreList = ['nri@casio.com', 'rims@caiso.com']
    for c in m.cc:
        if c.address.lower() not in ignoreList:
            list.append(c.address.lower()) 
    for t in m.to:
        if t.address.lower() not in ignoreList:
            list.append(t.address.lower())
    try:
        tables = pd.read_html(m.body)
    except:
        return False
    # get detail table
    projId = getFirstTable(tables[0], list)
    if projId == None:
        return True
    print('processed first table')
    # get bucket bucket progress
    getSecondTable(tables[1], projId)
    print('processed second table')
    # get project memo
    getThirdTable(tables[2], projId)
    print('processed third table')
    # #get bucket notes
    getFourthTable(tables[3], projId)
    print('processed fourth table')
    # #get meter devices
    getFifthTable(tables[4], projId)
    print('processed')
    return True

def getFirstTable(table, userList):
    # convert and transpose to list
    today = datetime.today()
    dict = table.fillna('None').transpose().to_dict('list')
    project = db.NRIMainProject.find_one({'isoNumber': dict[0][1]})
    dictionary = {
        "isoNumber": dict[0][1],
        "projectName": dict[1][1],
        "resourceId":dict[2][1],
        "project_fnm_build": dict[3][1],
        "point_of_delivery": dict[4][1], 
        "implementDate": dict[5][1],
        "status": "Active",
        "assign": userList,
        "updated": today,
        "notes": ""
    }
    if project == None:
        # add main project
        dictionary["completed"] = False
        dictionary["client"] = ""
        project = db.NRIMainProject.insert_one(dictionary)
        id = str(project.inserted_id)
    else:
        # check if project is completed
        if project["status"] != "Active":
            return None
        # update current project
        combinedList = list(set(userList) | set(project["assign"]))
        dictionary["assign"] = combinedList
        
        db.NRIMainProject.update_one({'isoNumber': dict[0][1]}, {"$set": dictionary})
        # check for resource id to match
        if project["resourceId"] != dictionary["resourceId"]:
            subject = "{} - {} Resource ID has been Assigned".format(project["isoNumber"], project["projectName"])
            db.emailLog.insert_one({
                "target": ["nri@gridsme.com", "vta@gridsec.com"],
                "status":"new",
                "subject": subject,
                "template": "nri_resource.html",
                "dict": {
                    "isoNumber": project["isoNumber"],
                    "projectName": project["projectName"],
                    "resourceId": dictionary["resourceId"]
                }
            })
        id = str(project["_id"])
    return id

# bucket progress
def getSecondTable(table, id):
    print(table["Bucket Item"])
    uniques = table["Bucket Item"].fillna('None').unique()
    bucketList = table.iloc[0].to_numpy()
    cleanedBucketList = []
    # clean bucket list
    for i in list(bucketList):
        if type(i) != str:
            i = ''
        cleanedBucketList.append(i)
    # remove first index of empty string
    cleanedBucketList.pop(0)

    
    template = db.NRITemplates.find().sort('number', pymongo.ASCENDING)
    project = db.NRIMainProject.find_one({"_id":ObjectId(id)})
    # create bucket item from template if doesn't exist
    for t in template:
        item = db.NRIBucketProgress.find_one({'projectId': id, "name": t["name"]})
        dictionary = {
            "projectId": id,
            "name": t["name"],
            "upload": "",
            "assign": [],
            "bucket_item_due_date": ""
        }
        if item == None:
            db.NRIBucketProgress.insert_one(dictionary)
    for u in uniques:
        # skip none
        if u != "None":
            # set up table
            row = table.loc[table["Bucket Item"] == u]
            dict = row.dropna(axis=1).set_index("Bucket Item").transpose().to_dict('list')
            index = db.NRITemplates.find_one({"name": u})
            # try to find in database nri template
            if index != None:
                item_due_date = cleanedBucketList[index['bucket_index']]
            else:
                item_due_date = ""
            for key, value in dict.items():
                # set up dictionary
                if value == []:
                    status = "NA"
                else:
                    status = value[0]
                # automatically mark as complete if date exists
                dictionary = {
                    "projectId": id,
                    "name": u,
                    "upload": status,
                    "assign": [],
                    "bucket_item_due_date": item_due_date
                }
                # look for bucket item in database
                item = db.NRIBucketProgress.find_one({"projectId": id, "name": u})
                if is_date(status):
                    dictionary['status'] = "Complete"
                if item == None:
                    db.NRIBucketProgress.insert_one(dictionary)
                else:
                    db.NRIBucketProgress.update_one({"_id":item["_id"]}, {"$set": dictionary})


def getThirdTable(table, id):
    #get third table project memo
    if table.empty:
        return
    table = table.fillna("NA")
    records = table.to_dict('records')
    for rec in records:
        item = db.NRIProjectMemo.find_one({'projectId':id, 'memo': rec['Project Memo']})
        dictionary = {"projectId": id, "date": rec["Date"], "memo": rec["Project Memo"], 'updated': rec["Updated By"]}
        if item == None:
            db.NRIProjectMemo.insert_one(dictionary)
        else:
            db.NRIProjectMemo.update_one({"_id":item["_id"]}, {"$set": dictionary})

# bucket notes item
def getFourthTable(table, id):
    if table.empty:
        return
    new_header = ["Bucket Item", "Bucket Note", "Last Updated"]
    table.columns = new_header
    table = table.fillna("NA")
    records = table.to_dict('records')
    for rec in records:
        item = db.NRIBucketNotes.find_one({"projectId": id, "bucketNote": rec["Bucket Note"]})
        dictionary = {"projectId": id, "bucketItem": rec["Bucket Item"], "bucketNote": rec["Bucket Note"], "updated": rec["Last Updated"]}
        if item == None:
            db.NRIBucketNotes.insert_one(dictionary)
        else:
            db.NRIBucketNotes.update_one({"_id": item["_id"]}, {"$set": dictionary})

def getFifthTable(table, id):
    #get fifth table meter devices
    if table.empty:
        return
    table = table.fillna("NA")
    records = table.to_dict('records')
    # remove all meter devices
    db.NRIMeterDevices.delete_many({"projectId": id})
    for rec in records:
        dictionary = {"projectId": id, "meterId": rec["Meter Device Id(s)"], "meterLabel": rec["Meter Label"], "updated": rec["Last Updated"]}
        db.NRIMeterDevices.insert_one(dictionary)

def is_date(string, fuzzy=False):
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except:
        return False