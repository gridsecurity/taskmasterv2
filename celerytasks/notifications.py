from datetime import datetime
from .conn import db

def notify(users, title, body, link=None, ticket=None, state=None):
    date = datetime.today()
    for user in users:
        baseDict = {
            "target": user,
            "date": date,
            "title": title,
            "body": body,
            "visible": True
        }
        if link != None:
            baseDict["link"] = link
        if ticket != None:
            # check if notification is exist for this person
            alerts = db.notifications.find_one({"ticket": ticket, "target": user, "visible": True})
            if alerts != None:
                print("found alert")
                continue
            baseDict["ticket"] = ticket
        if state != None:
            baseDict["state"] = state
        else:
            db.notifications.insert_one(baseDict)