from .conn import db
from O365 import Account, MSGraphProtocol
from .teamsMessage import Teams
import pymsteams
from io import BytesIO
import base64
from .cisa_processor import get_embedded_files
import pandas as pd
from datetime import datetime
from .s3 import S3_DB

import os

class EmailBox:
    def __init__(self, email, folder):
        dbcreds = db.accessList.find_one({"name": "o365 api"})
        creds = (dbcreds["appId"], dbcreds["secret"])
        protocol = MSGraphProtocol(api_version="beta")
        account = Account(creds,  auth_flow_type='credentials', tenant_id=dbcreds['tenantId'], protocol=protocol)
        if account.authenticate():
            self.account = account
            self.mailbox = account.mailbox(email).get_folder(folder_name=folder)
            self.email = email
        else:
            team = Teams("GS-DEV")
            team.send_message("Couldn't authenticate mailbox for {}".format(email))

    def send_email(self, targets, subject, body, cc=None, bcc=None, attachment=None, conversation_id=None):
        # convert string into array
        if type(targets) is str:
            targets = [targets]
        # get conversation id if exists
        if conversation_id:
            print("adding to existing conversation")
            query = self.account.mailbox(self.email).new_query().on_attribute('conversation_id').equals(conversation_id)
            messages = self.account.mailbox(self.email).get_messages(query=query)
            for m in messages:
                lastMessage = m
            print(lastMessage.object_id)
            reply = lastMessage.reply()
            # create clear methods
            reply.to.clear()
            reply.cc.clear()
            reply.body = body
            reply.to.add(list(map(lambda x: x.replace(" ", ""), targets)))
            if cc != None:
                for c in cc:
                    print('adding', c)
                    reply.cc.add(c.replace(" ", ""))
            if bcc != None:
                for bc in bcc:
                    print('adding', bc)
                    reply.bcc.add(bc.replace(" ", ""))
            # save the draft then send out
            reply.save_draft()
            # add attachment
            if attachment:
                s3 = S3_DB()
                for at in attachment:
                    try:
                        if at['source'] == 's3':
                            attach = s3.download_file(at["path"])
                            print(attach)
                            in_memory_attachment = (attach, at['filename'])
                            reply.attachments.add([in_memory_attachment])
                    except:
                        pass
        else:
            print("create new message")
            m = self.account.new_message(resource=self.email)
            m.subject = subject
            m.body = body
            # add to users
            m.to.add(list(set(targets)))
            if cc:
                m.cc.add(list(set(cc)))
            if bcc:
                m.bcc.add(list(set(bcc)))
            reply = m
        
        # add attachment
        if attachment:
            s3 = S3_DB()
            for at in attachment:
                try:
                    if at['source'] == 's3':
                        attach = s3.download_file(at["path"])
                        print(attach)
                        in_memory_attachment = (attach, at['filename'])
                        reply.attachments.add([in_memory_attachment])
                except:
                    pass
        reply.save_draft()
        try:
            m.send()
        except:
            pass


class NRIBox:
    def __init__(self, email, folder):
        dbcreds = db.accessList.find_one({"name": "NRI Email"})
        creds = (dbcreds["appId"], dbcreds["secret"])
        protocol = MSGraphProtocol(api_version="beta")
        account = Account(creds,  auth_flow_type='credentials', tenant_id=dbcreds['tenantId'], protocol=protocol)
        if account.authenticate():
            self.account = account
            self.mailbox = account.mailbox(email).get_folder(folder_name=folder)
        else:
            team = Teams("GS-DEV")
            team.send_message("Couldn't authenticate mailbox for {}".format(email))
        
    def send_message(self, url, message):
        teams = pymsteams.connectorcard(url)
        teams.text(message)
        teams.send()
            
class CISABox:
    def __init__(self, email, folder):
        dbcreds = db.accessList.find_one({'name': 'o365 api'})
        creds = (dbcreds['appId'], dbcreds['secret'])
        protocol = MSGraphProtocol(api_version="beta")
        self.account = Account(creds,  auth_flow_type='credentials', tenant_id=dbcreds['tenantId'], protocol=protocol)
        self.mailbox = self.account.mailbox(email).get_folder(folder_name=folder)
    
    def send_message(self, url, message):
        teams = pymsteams.connectorcard(url)
        teams.text(message)
        teams.send()
        
    def check_reports_inbox(self, target_email):
        if self.account.authenticate():
            query = self.mailbox.new_query().on_attribute("from").contains(target_email).chain("and").on_attribute("isRead").equals(False)
            messages = self.mailbox.get_messages(query=query, download_attachments=True)
            for m in messages:
                print(m.subject)
                # download file
                for f in m.attachments:
                    print(f.name)
                    try:
                        if ".pdf" in f.name:
                            fileObj = BytesIO(base64.b64decode(f.content))
                            fileObj.seek(0)
                            with open("temp.pdf", "wb") as file:
                                file.write(fileObj.read())
                            files = get_embedded_files("temp.pdf")
                            # loop through each file and import into database
                            for name, data in files.items():
                                if ".csv" in name:
                                    fileObj = BytesIO(data)
                                    fileObj.seek(0)
                                    df = pd.read_csv(fileObj)
                                    df = df.fillna("")
                                    df["date"] = datetime.timestamp(m.received)
                                    df["filename"] = name
                                    records = df.to_dict("records")
                                    if len(records) > 0:
                                        db.cisa_report.insert_many(records)
                            # delete temp file
                            os.remove("temp.pdf")
                        m.mark_as_read()
                        request_url = 'https://gridsec.webhook.office.com/webhookb2/765cfca8-8ff7-42a5-b455-50802ac57775@9542b69d-0d8b-4244-8f4f-debecdbdc2b5/IncomingWebhook/c68585d562194ba4841985d656f11986/096bc56c-47ed-4dce-a63a-5bb9c1a57a08'
                        self.send_message(request_url, 'Finished Processing CISA report {}'.format(m.received))
                    except:
                        pass
