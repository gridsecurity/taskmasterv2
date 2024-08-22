import json
import requests
from .conn import db 

class Pagerduty:
    def __init__(self):
        self.portal_url = 'https://portal.gridsec.com/tickets/details/'
        self.url = "https://api.pagerduty.com/incidents"
        self.headers = {
        'Authorization': 'Token token=u+76i25R_HiydvT-k7cA',
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Content-Type': 'application/json',
        'From': 'tickets@gridsec.com',
        'Content-Type': 'application/json'
    }

    def createIncident(self, requester, number, subject):
        serviceId = ['PGU4ORO']
        payload = json.dumps({
            "incident": {
                "type": "incident",
                "title": "{}|{}|{}".format(requester, number, subject),
                "service": {
                    "id": serviceId,
                    "type": "service_reference",
                    "summary": "{}|{}|{}".format(requester, number, subject)
                },
                "urgency": "high",
                "body":{
                    "type":"string",
                    "details": "{}{}".format(self.portal_url , number)
                }
            }
        })
        r = requests.post(self.url, data=payload, headers=self.headers)
        db.tickets.update_one({"number": number}, {"$set": {"pagerduty_id": r.json()}})
        return r
    
    def create_ticket_alert(self, tickets):
        for tick in tickets:
            print('sending pagerduty {}'.format(tick['number']))
            if "pagerduty_id" not in tick.keys():
                if tick["type"] == "incident":
                    subject = tick["subject"]
                else:
                    subject = tick["reason"]
                # if from crowdstrike set urgency to high
                urgency = "low"
                if tick["requester"] == "falcon@crowdstrike.com":
                    urgency = "high"
                if tick["severity"] == 1:
                    urgency = "high"

                serviceIds = ['PGU4ORO']
                for serviceId in serviceIds:
                    payload = json.dumps({
                        "incident": {
                            "type": "incident",
                            "title": "{}|{}|{}".format(tick["requester"], tick["number"], subject),
                            "service": {
                                "id": serviceId,
                                "type": "service_reference",
                                "summary": "{}|{}|{}".format(tick["requester"], tick["number"], subject)
                            },
                            "urgency": urgency,
                            "body":{
                                "type":"string",
                                "details": "{}{}".format(self.portal_url, tick["number"])
                            }
                        }
                    })
                    r = requests.post(self.url, data=payload, headers=self.headers)
                db.tickets.update_one({"number": tick["number"]}, {"$set": {"pagerduty_id": r.json()}})