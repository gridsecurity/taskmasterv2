from datetime import datetime
from bson.objectid import ObjectId

from .conn import *
from .okta import OKTA
from .taskClass import Tasks

class Provisions:
    def __init__(self):
        self.time_now = int(datetime.timestamp(datetime.today()))
        self.time_frame = {"$gte": self.time_now - 60, "$lte": self.time_now} # 1 minutes
        self.key = db.accessList.find_one({"name" :"GridSec Okta"})["key"]
        self.okta = OKTA("https://gridsec.okta.com/api/v1/", self.key)

    def add_provision(self):
        tickets = db.tickets.find({"type": "access", "status": "approved", "startDate": self.time_frame})
        for t in tickets:
            # check if ticket has provision or deprovison tasks
            tasks = list(db.tasks.find({"ticket": str(t["_id"]), "status": "new", "action": "Provision"}))
            if len(tasks) > 0:
                user = self.okta.get_user(t["email"]).json()[0]
                for g in t["electronic_access"]:
                    group = db.group_provisions.find_one({"_id": ObjectId(g)})
                    db.group_provisions.update_one({"_id": group["_id"]}, {"$addToSet": {"members": t["email"]}})
                    if "oktaGroupId" in group.keys() and group["auto_provision"]:
                        res = self.okta.provision_user(group["oktaGroupId"], user["id"])
                        if res.status_code == 204:
                            # update ticket and internal note
                            db.tickets.update_one({"_id": t["_id"]}, {"$set": {"status": "active", "active_date": self.time_now}})
                            db.ticketNotes.insert_one({
                                "username": "Okta Bot",
                                "ticketId": str(t["_id"]),
                                "notes": "Added {} to {}".format(t["email"], group["groupName"]),
                                "datetime": self.time_now,
                                "noteType": "external"
                            })
                            if user["id"] not in list(map(lambda x: x["id"], group["members"])):
                                print("adding user")
                                db.group_provisions.update_one({"_id": ObjectId(g)}, {"$push": {"members": user}})
                            for task in tasks:
                                taskItem = Tasks(id=task["_id"])
                                taskItem.update_task("status", "complete", "Portal Bot")
                            
                        else:
                            # notify service desk
                            db.emailLog.insert_one({
                                "target": ["vta@gridsec.com", "bbarnes@gridsec.com"],
                                "status": "new",
                                "subject": "A group failed to provision",
                                "template": "default.html",
                                "dict": {
                                    "title": "Group {} failed to provision for {}".format(group["groupName"], t["email"])
                                }
                            })
    def deprovision(self):
        tickets = list(db.tickets.find({"type": "access", "status": "active", "endDate": self.time_frame}))
        for t in tickets:
            tasks = list(db.tasks.find({"ticket": str(t["_id"]), "status": "new", "action": "Deprovision"}))
            if len(tasks) > 0:
                user = self.okta.get_user(t["email"]).json()[0]
                for g in t["electronic_access"]:
                    group = db.group_provisions.find_one({"_id": ObjectId(g)})
                    db.group_provisions.update_one({"_id": group["_id"]}, {"$pull": {"members": t["email"]}})
                    if "oktaGroupId" in group.keys() and group["auto_provision"]:
                        res = self.okta.deprovision_user(group["oktaGroupId"], user["id"])
                        if res.status_code == 204:
                            # update ticket and internal note
                            db.tickets.update_one({"_id": t["_id"]}, {"$set": {"status": "disabled"}})
                            db.ticketNotes.insert_one({
                                "username": "Okta Bot",
                                "ticketId": str(t["_id"]),
                                "notes": "Removed {} to {}".format(t["email"], group["groupName"]),
                                "datetime": self.time_now,
                                "noteType": "internal"
                            })
                            db.group_provisions.update_one({"_id": ObjectId(g)}, {"$pull": {"members": {"id": user["id"]}}})
                            for task in tasks:
                                taskItem = Tasks(id=task["_id"])
                                taskItem.update_task("status", "complete", "Portal Bot")
                        else:
                            print('notify service desk')
                            # notify service desk
                            db.emailLog.insert_one({
                                "target": ["vta@gridsec.com", "bbarnes@gridsec.com"],
                                "status": "new",
                                "subject": "A group failed to provision",
                                "template": "default.html",
                                "dict": {
                                    "title": "Group {} failed to provision for {}".format(group["groupName"], t["email"])
                                }
                            })