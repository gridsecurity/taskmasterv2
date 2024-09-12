from datetime import datetime, timedelta
from io import BytesIO
import base64
import lxml.html.clean
from django.template.loader import render_to_string
from .conn import db
from bson import ObjectId
from hashlib import md5
import re
import pymongo
from .splunk_logs import create_splunk_log
from .pagerduty import Pagerduty
from .s3 import S3_DB
from .notifications import notify
import os
from bs4 import BeautifulSoup

class TicketProcessor:
    def __init__(self, message, user_id, account):
        self.m = message
        self.user_id = user_id
        self.account = account

    def setDict(self, type):
        count = db.tickets.find({}).sort("number", pymongo.DESCENDING)[0]['number'] + 1 # add 1 count to ticket
        to = []
        cc = []
        for t in self.m.to:
            to.append(t.address)
        try:
            for c in self.m.cc:
                cc.append(c.address)
        except:
            pass
        print('creating dict')
        dict = {
            "number": count,
            "type": type,
            "submitdate": datetime.timestamp(datetime.today()),
            "updated": datetime.timestamp(datetime.today()),
            "subject": self.m.subject,
            "requester": self.m.sender.address,
            "to": to,
            "cc": cc,
            "name": self.m.sender.name,
            "body": lxml.html.clean.clean_html(self.m.body),
            "sites": [],
            "devices": [],
            "dg": [],
            "status":"new",
            "severity": 4,
            "conversation_id": self.m.conversation_id
        }
        if self.m.sender.address == "clrwy-fs@gridsec.com":
            dict["severity"] == 1
        return dict
    
    def create_ticket(self, dict):
        print("creating new ticket")
        print(dict)
        res = db.tickets.insert_one(dict)
        self.id = str(res.inserted_id)
        if dict["severity"] == 1:
            pager = Pagerduty()
            pager.createIncident(dict['requester'], dict['number'], "Sev 1 incident")
        # upload attachments
        if self.m.has_attachments:
            self.upload_sftp(str(dict["number"]))
        # send reply email
        print("sending reply email")
        template = render_to_string('emailadmin/support_ticket_email.html', dict)
        reply_msg = self.m.reply()
        reply_msg.body = template
        try:
            reply_msg.send()
        except:
            pass
        return dict
    
    def upload_sftp(self, path):
        soup = BeautifulSoup(self.m.body, 'html.parser')
        for file in self.m.attachments:
            file_name = file.name
            file_extension = os.path.splitext(file.name)[1]
            print(file.attachment_type)
            
            if file.attachment_type == "item":
                custom_url = "https://graph.microsoft.com/beta/users/{}/messages/{}/attachments/{}/$value".format(self.user_id, self.m.object_id, file.attachment_id)
                response = self.account.connection.get(custom_url)
                if response.status_code == 200:
                    print("EML content retrieved, preparing to upload.")
                    eml_content = BytesIO(response.text.encode('utf-8'))
                    eml_file_path = '{}/{}'.format(path, file.name+".eml")
                    print('uploading {}'.format(file.name))
                    s3 = S3_DB()
                    s3.upload_file(eml_content, eml_file_path)
            else:
                fileObj = BytesIO(base64.b64decode(file.content))
                md5sum = md5(fileObj.getbuffer())
                if db.ignoreFileList.find_one({'hash': md5sum.hexdigest()}) == None:
                    # go through the images in the body and replace the cid with portal url
                    for img_tag in soup.find_all('img', src=True):
                        if img_tag['src'].startswith('cid:'):
                            content_id = img_tag['src'][4:] 
                            # Extract the cid and compare with file content_id
                            if content_id == file.content_id:
                                file_name = f"{file.content_id}{file_extension}"
                                img_tag['src'] = f'/api/tickets/images?id={self.id}&file_name={"{}/{}".format(path, file_name)}'
                                img_tag['alt'] = file_name
                    print('uploading {}'.format(file.name))
                    s3 = S3_DB()
                    s3.upload_file(fileObj, "{}/{}".format(path, file_name))
        if soup.body:
            soup = str(soup.body.decode_contents())  
        else:
            soup = str(soup) 
        print(f"soup: {soup}")
        db.tickets.update_one({"_id": ObjectId(self.id)}, {"$set": {"body":soup}})
        return soup

    def message_check(self):
        seven_days_ago = datetime.today() - timedelta(days=7)
        # check for conversation id
        ticket = list(db.tickets.find({"conversation_id": self.m.conversation_id}).sort('_id', pymongo.DESCENDING).limit(1))
        if len(ticket) != 0:
            return ticket[0]
        # check for object in body
        pattern = '.*?###---\[(\w*)]---###.*'
        objectid = re.search(pattern, self.m.body)
        if objectid != None:
            print('object id exists')
            ticket = db.tickets.find_one({"_id":ObjectId(objectid.group(1))})
            if ticket != None:
                print('return ticket')
                return ticket
        # search through all for subject
        rePattern = re.compile(r"^RE: ", re.IGNORECASE)
        if self.m.subject:
            reResult = rePattern.search(self.m.subject)
            subject = self.m.subject.replace("RE: ", "")
            subject = subject.replace("Re: ", "")
            subject = subject.replace("FW: ", "")
            if reResult != None:
                print('matched RE: Subject')
                # try and search db for ticket
                tickDict = {
                    "$or":[
                        {"submitdate": {"$gte": seven_days_ago}},
                        {"updated": {"$gte": seven_days_ago}}
                    ],
                    "subject": subject,
                    "status":{"$nin": ["closed", "deleted", "merged"]}
                }
                tickets = db.tickets.find(tickDict).sort("number",pymongo.DESCENDING)
                if db.tickets.count_documents(tickDict) != 0:
                    return tickets[0]
            # if all else fails try and find matching subject
            subjectDict = {
                "$or":[
                    {"submitdate": {"$gte": seven_days_ago}},
                    {"updated": {"$gte": seven_days_ago}}
                ],
                "subject": subject}
            tickets = db.tickets.find(subjectDict).sort("number", pymongo.DESCENDING)
            if db.tickets.count_documents(subjectDict) != 0:
                return tickets[0]
        return None
    
    def process_ticket(self):
        # create alerts
        if self.m.sender.address in ["falcon@crowdstrike.com", "noreply+api.alerter@sbenergy.logicmonitor.com"]:
            dict = self.setDict("alert")
            # create splunk log
            if self.m.sender.address == "alerts@gridsec.com":
                create_splunk_log(self.m)
            self.create_ticket(dict)
            return
        # blacklist emails
        if self.m.sender.address in db.accessList.find_one({"name":"Email Black List"})["emails"]:
            print("email blacklisted")
            return
        # set dictionary
        dict = self.setDict("incident")
        # check for existing ticket
        print('checking message')
        ticket = self.message_check()
        if ticket != None:
            print("ticket exists")
            self.process_existing_ticket(ticket)
        else:
            tick = self.create_ticket(dict)

    def process_existing_ticket(self, ticket):
        self.id = str(ticket["_id"])
        # check if ticket is closed and older than 3 days will generate a new ticket
        if ticket['status'] in ['disabled', 'resolved', 'closed', 'completed_change']:
            if "closed_date" not in ticket.keys():
                # create new ticket
                dict = self.setDict("incident")
                tick = self.create_ticket(dict)
                # link both tickets
                db.tickets.update_one({"number": tick["number"]}, {"$push": {"reference": str(ticket["_id"])}})
                db.tickets.update_one({"_id": ticket["_id"]}, {"$push": {"reference": str(tick["_id"])}})
            else:
                # if date is greater than 3 days
                if datetime.fromtimestamp(ticket["closed_date"]) < datetime.today() - timedelta(days=3):
                    dict = self.setDict("incident")
                    tick = self.create_ticket(dict)
                    # link both tickets
                    db.tickets.update_one({"number": tick["number"]}, {"$push": {"reference": str(ticket["_id"])}})
                    db.tickets.update_one({"_id": ticket["_id"]}, {"$push": {"reference": str(tick["_id"])}})
                else:
                    # re-open ticket
                    self.add_to_existing_ticket(ticket)
                    # create new incident for pagerduty
                    print('creating new incident')
                    pager = Pagerduty()
                    pager.createIncident(ticket['requester'], ticket['number'], "Ticket has been reoepend")
        else:
            self.add_to_existing_ticket(ticket)
    
    def add_to_existing_ticket(self, ticket):
        if self.m.has_attachments:
            updated_body = self.upload_sftp(str(ticket["number"]))
        else:
            updated_body = self.m.body
        # add note
        to = []
        cc = []
        for t in self.m.to:
            to.append(t.address)
        try:
            for c in self.m.cc:
                cc.append(c.address)
        except:
            pass
        print(self.m.to)
        print(self.m.cc)
        db.ticketNotes.insert_one({
            "username": self.m.sender.address,
            "ticketId": str(ticket["_id"]),
            "notes": updated_body,
            "to": to,
            "cc": cc,
            "datetime": datetime.timestamp(datetime.today()),
            "noteType": "external"
        })
        # set converstaion id on ticket update
        updateDict = {
            "conversation_id": self.m.conversation_id, 
            "updated": datetime.timestamp(datetime.today())
        }
        gridsecUsers = db.users.distinct('username', {"teams": "GridSec"})
        if self.m.sender.address in gridsecUsers:
            status = "pending"
        else:
            status = "user_responded"
            updateDict["external_update"] = datetime.timestamp(datetime.today())
        if ticket["type"] == "incident":
            updateDict["status"] = status
        db.tickets.update_one({"_id": ticket["_id"]}, {"$set": updateDict})
        if "assign" in ticket.keys():
            notify(
                [ticket["assign"]], 
                "#{}".format(ticket["number"]), 
                "A new message from {}".format(self.m.sender.address),
                ticket=ticket["number"]
            )