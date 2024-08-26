from .conn import db
from .okta import OKTA


def okta_group_sync():
    print('syncing okta gorups')

    def process_group(g, okta, oktaOrgId):
        print(g["profile"]["name"])
        # do not process everyone
        if g["profile"]["name"] == "Everyone":
            return
        groupDict = {
            "groupName": g["profile"]["name"],
            "description": g["profile"]["description"],
            "active": True,
            "siteId": [],
            "orgId": [],
            "auto_provision": True,
            "provision_type": "Electronic",
            "security": True,
            "distribution": False,
            "members": [],
            "oktaGroupMembers": [],
            "oktaGroupId": g["id"],
            "oktaOrg": oktaOrgId
        }
        users = okta.get_group_users(g["id"]).json()
        sites = db.sites.find()
        for u in users:
            user = db.users.find_one({"username": u["profile"]["email"].lower()})
            # create user if not exist
            if user == None:
                user_dict = {
                    "username": u["profile"]["email"].lower(),
                    "group": [],
                    "sites": [],
                    "fullReport": False,
                    "site_list": [],
                    "report_sites": [],
                    "dgReport": False,
                    "logo": "",
                    "signature": "",
                    "firstName": u["profile"]["firstName"],
                    "lastName": u["profile"]["lastName"],
                    "cpuc_clients": [],
                    "teams": [],
                    "region": "",
                    "active": False
                }
                db.users.insert_one(user_dict)
            user = db.users.find_one({"username": u["profile"]["email"].lower()})
            groupDict["members"].append(str(user["_id"]))
            groupDict["oktaGroupMembers"].append(str(user["_id"]))
        group = db.group_provisions.find_one({"oktaGroupId": g["id"]})
        # only update certain fields if group exists
        if group:
            db.group_provisons.update_one({"oktaGroupId": g["id"]}, {"$set": {
                "oktaGroupMembers": groupDict["oktaGroupMembers"],
                "groupName": g["profile"]["name"],
                "description": g["profile"]["description"]
            }})
        else:
            # find site id from sitename
            for s in sites:
                if s["site"].lower() in groupDict["groupName"].lower():
                    print(s["site"])
                    groupDict["siteId"] = [str(s["_id"])]
                    # find owner group
                    groupDict["orgId"] = [str(db.groups.find_one({"name": s["owner"]})["_id"])]
                    
                if s["label"].lower() in groupDict["groupName"].lower():
                    print(s["site"])
                    groupDict["siteId"] = [str(s["_id"])]
                    groupDict["orgId"] = [str(db.groups.find_one({"name": s["owner"]})["_id"])]
            db.group_provisions.update_one({"oktaGroupId": g["id"]}, {"$set": groupDict}, upsert=True)

    # process gridsec okta
    gridsec_env = db.accessList.find_one({"name": "GridSec Okta"})
    gridsec_okta = OKTA(gridsec_env["url"], gridsec_env["key"])
    groups = gridsec_okta.get_groups().json()
    for g in groups:
        process_group(g, gridsec_okta, "gridsec")
    # process c4 okta
    c4_env = db.accessList.find_one({"name": "C4 Okta"})
    c4_okta = OKTA(c4_env["url"], c4_env["key"])
    groups = c4_okta.get_groups().json()
    for g in groups:
        process_group(g, c4_okta, "c4")