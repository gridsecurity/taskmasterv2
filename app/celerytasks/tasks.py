from datetime import datetime, date, timedelta
from jinja2 import Environment, FileSystemLoader
from time import strftime, localtime
from celery import shared_task
from bson.objectid import ObjectId
import json
import os

from .conn import *
from .splunk_cloud_assets import splunk_cloud_assets_push
from .emailbox import EmailBox, NRIBox
from .ticket_processor import TicketProcessor
from .teamsMessage import Teams
from .request_emails import request_email_processor
from .nri_email_parser import procMessage
from .pagerduty import Pagerduty
from .industrial_defender import Industrial_Defender
from .helpers import convert_tickets_to_excel, upload_to_sharepoint
from .sync_patches import sync_asset_patches
# from .provisions import Provisions
from .s3 import S3_DB
from .emailbox import CISABox
from .asset_dump import dump_assets
import time
from .ninja_one import NinjaOne
from .auvik import Auvik
from .okta import OKTA
import shutil


@shared_task(name="list_time")
def list_time():
    print(datetime.today())
    # db.emailLog.insert_one({
    #     "target": "vta@gridsec.com",
    #     "status": "new",
    #     "subject": "Test email subject",
    #     "template": "default.html",
    #     "dict": {
    #         "body": "<p>The time is {}".format(datetime.today()),
    #         "title": "This is a test email for celery task"
    #     }
    # })

@shared_task(name="splunk_cloud_assets")
def splunk_cloud_assets():
    splunk_cloud_assets_push()


@shared_task(name="process_tickets_emails")
def process_ticket_emails():
    print("process ticket email")
    # process unsent messages
    draft = EmailBox('tickets@gridsec.com', 'Drafts')
    unsent = draft.mailbox.get_messages()
    for m in unsent:
        try:
            to_users = []
            for to in m.to:
                to_users.append(to.address)
            if len(to_users) == 0:
                m.delete()
            else:
                m.send()
        except:
            team = Teams("GS-DEV")
            team.send_message('An email did not send out. Go to tickets inbox and fix it!')
    # get messages
    inbox = EmailBox('tickets@gridsec.com', "Inbox")
    messages = inbox.mailbox.get_messages(query="isRead eq false", download_attachments=True)
    for m in messages:
        ticket = TicketProcessor(m)
        ticket.process_ticket()
        m.mark_as_read()
    

@shared_task(name="request_emails")
def process_request_emails():
    print("processing request emails")
    inbox = EmailBox("requests@gridsec.com", "Inbox")
    messages = inbox.mailbox.get_messages(query="isRead eq false", download_attachments=True)
    for m in messages:
        request_email_processor(m)

@shared_task(name="nri_email")
def nri_email():
    print("checking nri email")
    inbox = NRIBox('nri@gridsme.com', "Inbox")
    query = inbox.account.mailbox('nri@gridsme.com').new_query().on_attribute('from').equals('rims-noreply@caiso.com').chain('and').on_attribute('isRead').equals(False).chain('and').on_attribute('subject').contains('Your FNM Project Auto Update')
    messages = inbox.mailbox.get_messages(query=query, limit=999)
    digest = []
    for m in messages:
        res = procMessage(m)
        if res == True:
            m.mark_as_read()
            digest.append(m.subject)
    # get uploaded files list
    todaysDate = date.today()
    yesterday = datetime.strptime(str(todaysDate), '%Y-%m-%d') - timedelta(days=1)
    body = ''
    if len(digest) != 0:
        body += "<p>Projects that are updated </p><p>{}</p>".format('<br>'.join(digest))
    filesDict = {"bucketProgressId":{"$exists": True}, "date":{"$gte": yesterday}}
    files = db.s3Objects.find(filesDict)
    if db.s3Objects.count_documents(filesDict) > 0:
        # loop through each file and get info
        body += "<p>Files Uploaded</p>"
        for f in files:
            project = db.NRIMainProject.find_one({"_id":ObjectId(f["projectId"])})
            bucket = db.NRIBucketProgress.find_one({"_id":ObjectId(f["bucketProgressId"])})
            body += "<p>{} - {} - {} - {} </p>".format(project["isoNumber"], project["projectName"], bucket["name"], f["fileName"])
    # check for COD date
    # check day of the week
    dayOftheWeek = datetime.today().weekday()
    # every thursday check all projects for COD date due
    if dayOftheWeek == 3:
        findDict = {"cod": {"$lte": datetime.today()}, "completed": False}
        if db.NRIMainProject.count_documents(findDict) != 0:
            projects = db.NRIMainProject.find(findDict)
            body += "<p>Passed due projects</p>"
            for proj in projects:
                body += "<p>{} - {} - {}</p>".format(proj["isoNumber"], proj["projectName"], proj["cod"])

    # send an email for updated projects
    if len(digest) != 0 or db.s3Objects.count_documents(filesDict) != 0:
        new_mail = inbox.mailbox.new_message()
        new_mail.to.add('nri@gridsme.com')
        new_mail.to.add('vta@gridsme.com')
        new_mail.subject = "NRI Updated projects"
        new_mail.body = body
        new_mail.send()
    # send confirmation that it has processed
    request_url = 'https://gridsec.webhook.office.com/webhookb2/765cfca8-8ff7-42a5-b455-50802ac57775@9542b69d-0d8b-4244-8f4f-debecdbdc2b5/IncomingWebhook/c68585d562194ba4841985d656f11986/096bc56c-47ed-4dce-a63a-5bb9c1a57a08'
    inbox.send_message(request_url, 'Finished processing NRI emails')



@shared_task(name="pagerduty")
def pagerduty():
    print('checking pagerduty')
    findDict = {
        "type":{"$in":["incident", "access", "tca_rm"]},
        "severity": {"$in": [1,2]},
        "status":{ "$in":["new","pending","user_responded","approved", "approve", "active"]}, 
        "teams": {"$exists": 0}, "assign":{"$exists":0}, 
        "pagerduty_id":{"$exists": 0}
    }
    
    if db.tickets.count_documents(findDict) > 0:
        tickets = db.tickets.find(findDict)
        # send email to pagerduty
        pager = Pagerduty()
        pager.create_ticket_alert(tickets)



@shared_task(name="id_dump")
def id_asset_dump():
    defender = Industrial_Defender()
    locations = []
    for item in defender.get_admin_props():
        # get unique values for locations
        for prop in item["adminProperties"]:
            if prop["name"] == "Location":
                if prop["value"] not in locations:
                    locations.append(prop["value"])
    # update location list
    db.accessList.update_one({"name": "id_asset_locations"}, {"$set": {"locations": locations}})
    today_date = datetime.timestamp(datetime.today())
    for location in locations:
        total_asset_count = defender.get_location_asset_count(location)
        location_assets = defender.get_state_data_for_assets(location, total_asset_count)
        for asset in location_assets:
            asset["manual"] = False
            asset["location"] = location
            asset["manual"] = False
            asset["lastUpdated"] = today_date
            db.id_assets.update_one({"assetUuid": asset["assetUuid"]}, {"$set": asset}, upsert=True)
    teams = Teams("GS-DEV")
    teams.send_message("Finished processing Industrial Defender Assets")

@shared_task(name="ninja_one_dump")
def ninja_one_dump():
    ninja = NinjaOne()
    print( "Pulling NinjaOne Objects")
    after = 0
    start = time.time()
    while True:
        devices = ninja.list_devices_detailed(page_size=500, after=after)
        if len(devices) > 0:
            for d in devices:
                db.ninja.update_one({"id": d["id"]}, {"$set": d}, upsert=True)
            after += 500
        else:
            break

    finish = time.time()
    difference = (finish - start ) / 60
    print(difference)

@shared_task(name="auvik_dump")
def auvik_dump():
    auvik = Auvik()
    start = time.time()
    # Nightly pull of Auvik Assets
    print( "Pulling Auvik Objects" )
    deviceTypes = ["unknown", "switch", "l3Switch", "router", "accessPoint", "firewall", "workstation", "server", "storage", "printer", "copier", "hypervisor", "multimedia", "phone", "tablet", "handheld", "virtualAppliance", "bridge", "controller", "hub", "modem", "ups", "module", "loadBalancer", "camera", "telecommunications", "packetProcessor", "chassis", "airConditioner", "virtualMachine", "pdu", "ipPhone", "backhaul", "internetOfThings", "voipSwitch", "stack", "backupDevice", "timeClock", "lightingDevice", "audioVisual", "securityAppliance", "utm", "alarm", "buildingManagement", "ipmi", "thinAccessPoint", "thinClient"]
    for t in deviceTypes:
        devices = auvik.get_devices(deviceType=t)
        if 'data' in devices.keys():
            for d in devices["data"]:
                db.auvik.update_one({"id": d["id"]}, {"$set": d}, upsert=True)
            while True:
                if 'links' in devices.keys():
                    if "next" in devices["links"].keys():
                        url = devices["links"]["next"].split("&tenants=")[0]
                        devices = auvik.get_devices_url(url)
                        for d in devices["data"]:
                            db.auvik.update_one({"id": d["id"]}, {"$set": d}, upsert=True)
                    else:
                        break
                else:
                    break

    finish = time.time()
    difference = (finish - start ) / 60
    print(difference)
    print( "Pulling Auvik Network Objects" )
    start = time.time()
    networks = auvik.get_networks()
    if networks:
        for n in networks['data']:
            db.auvik_networks.update_one({'id' : n['id']}, {'$set' : n}, upsert=True)
        while True:
            if "next" in networks['links'].keys():
                url = networks["links"]["next"].split("&tenants=")[0]
                networks = auvik.get_networks_url(url)
                for n in networks['data']:
                    db.auvik_networks.update_one({'id' : n['id']}, {'$set' : n}, upsert=True)
            else:
                break
    finish = time.time()
    difference = (finish - start ) / 60
    print(difference)


@shared_task(name="asset_dump")
def asset_dump():
    dump_assets()

@shared_task(name="daily_tickets_report")
def daily_tickets_report():
    # upload open tickets
    open_tickets = list(db.tickets.find({
        "type": {"$nin": ["alert", "GOCIP", "project"]},
        "status": {"$nin": ["active", "disabled", "denied","draft", "completed", "cancelled", "completed_change", "cab_denied", "approver_denied","closed", "resolved", "deleted", "merged", "closed/skipped", "rolled_back"]}
    }, {"_id": 1, "type": 1, "number": 1, "status": 1, "subject": 1, "requester": 1, "assign": 1, "submitdate": 1, "sites": 1, "assign": 1, "updated": 1, "severity": 1, "scope": 1 }))
    excelFile = convert_tickets_to_excel(open_tickets)
    upload_to_sharepoint(excelFile, 'Shared Documents/Tickets-Reporting/Open-Tickets')
    # upload expired tickets
    expired_tickets = list(db.tickets.find({
        "type": "access",
        "status": "active",
        "endDate": {"$lte": datetime.timestamp(datetime.today())}
    }, {"_id": 1, "type": 1, "number": 1, "status": 1, "subject": 1, "requester": 1, "email": 1, "fullname": 1, "assign": 1, "submitdate": 1, "sites": 1, "endDate": 1, "assign": 1, "updated": 1, "severity": 1, "scope": 1  }))
    expiredExcel = convert_tickets_to_excel(expired_tickets)
    upload_to_sharepoint(expiredExcel, 'Shared Documents/Tickets-Reporting/Expired-Tickets')



@shared_task(name="pull_patches")
def sync_patches():
    sync_asset_patches()
    

@shared_task(name="splunk_cloud_assets")
def splunk_cloud_assets():
    assets = list(db.assets.find({}))
    event_list = []
    for a in assets:
        a.pop("_id")
        print(a["assetName"])
        if a["siteId"]:
            site = db.sites.find_one({"_id": ObjectId(a["siteId"])})
            a["ip"] = a["ipAddresses"]
            a["site_name"] = site["site"]
            if "latitude" in site.keys():
                a["lat"] = site["latitude"]
                a["long"] = site["longitude"]
        event_list.append({"event": a, "index": "asset_inventory_customers", "sourcetype": "_json"})
    json_objects = json.dumps(assets, indent=4)
    with open('asset.json', "w") as outfile:
        outfile.write(json_objects)


# @shared_task(name="access_ticket_provisions")
# def access_ticket_provisions():
#     provision = Provisions()
#     provision.add_provision()
#     provision.deprovision()
    

@shared_task(name="cisa_report")
def process_csa_report():
    mailbox = EmailBox("reports@gridsec.com", "Inbox")

    mailbox = CISABox('reports@gridsec.com', "Inbox")
    request_url = 'https://gridsec.webhook.office.com/webhookb2/765cfca8-8ff7-42a5-b455-50802ac57775@9542b69d-0d8b-4244-8f4f-debecdbdc2b5/IncomingWebhook/c68585d562194ba4841985d656f11986/096bc56c-47ed-4dce-a63a-5bb9c1a57a08'
    mailbox.send_message(request_url, "Running CISA Report")
    mailbox.check_reports_inbox("reports@cyber.dhs.gov")
    

@shared_task(name="clear_temp_s3")
def clear_temp_s3():
    s3 = S3_DB()
    for item in s3.list_bucket_items(os.environ.get("TICKET_BUCKET"), "temp"):
        s3.deleteFile(item.bucket_name, item.key)

@shared_task(name="send_emails")
def send_emails():
    print("sending emails")
    count = 0
    emails = db.emailLog.find({"status": "new"}).limit(50)
    failedCount = 0
    mailbox = EmailBox('tickets@gridsec.com', 'Inbox')
    for email in emails:
        # try:
            # send email
            try:
                if "startDate" in email["dict"].keys():
                    email["dict"]["startDate"] = strftime('%Y-%m-%d %H:%M:%S', localtime(int(email["dict"]["startDate"])))
            except:
                pass
            try:
                if "endDate" in email["dict"].keys():
                    email["dict"]["endDate"] = strftime('%Y-%m-%d %H:%M:%S', localtime(int(email["dict"]["endDate"])))
            except:
                pass
            template_loader = FileSystemLoader("emailadmin/templates/emailadmin")
            templateEnv = Environment(loader=template_loader)
            template = templateEnv.get_template(email["template"])
            html = template.render(email["dict"])
            print(html)
            # try and get options
            try:
                cc=email["cc"]
            except:
                cc=None
            try:
                bcc=email["bcc"]
            except:
                bcc=None
            try:
                attachment=email["attachment"]
            except:
                attachment=None
            try:
                conversation_id = email["conversation_id"]
            except:
                conversation_id = None
            mailbox.send_email(email['target'], email['subject'], html, cc, bcc, attachment=attachment, conversation_id=conversation_id)
            # update email log
            db.emailLog.update_one({"_id":email["_id"]}, {"$set":{"status":"sent", "sentDate": datetime.timestamp(datetime.today())}})
            count += 1
            print("sent email")
        # except Exception as e:
        #     print(e)
        #     failedCount += 1
        #     db.emailLog.update_one({"_id":email["_id"]}, {"$set":{"status":"failed"}})
        #     request_url = 'https://gridsec.webhook.office.com/webhookb2/765cfca8-8ff7-42a5-b455-50802ac57775@9542b69d-0d8b-4244-8f4f-debecdbdc2b5/IncomingWebhook/c68585d562194ba4841985d656f11986/096bc56c-47ed-4dce-a63a-5bb9c1a57a08'
        #     messageTeams = pymsteams.connectorcard(request_url)
        #     messageTeams.text('Something broke sending out check the database! {}'.format(e))
        #     messageTeams.send()


@shared_task(name="sync_okta_groups")
def syncOktaGroups():
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
    # gridsec_okta = OKTA(os.environ.get("GRIDSEC_OKTA_URL"), os.environ.get("GRIDSEC_OKTA_API_KEY"))
    # groups = gridsec_okta.get_groups().json()
    # for g in groups:
    #     process_group(g, gridsec_okta, "gridsec")
    # process c4 okta
    c4_okta = OKTA(os.environ.get("C4_OKTA_URL"), os.environ.get("C4_OKTA_API_KEY"))
    groups = c4_okta.get_groups().json()
    for g in groups:
        process_group(g, c4_okta, "c4")
    

@shared_task(name="sync_db")
def sync_db():
    prod_string = "mongodb+srv://root_user:{}@{}.awytu.mongodb.net".format(os.environ.get("DB_PASSWORD"), "prodcluster")
    preprod_string = "mongodb+srv://root_user:{}@{}.awytu.mongodb.net".format(os.environ.get("DB_PASSWORD"), "preprod")

    os.system('mongodump {}/{}'.format(prod_string, "dashboard"))
    os.system('mongorestore --drop dump/dashboard {}/{} --verbose'.format(preprod_string, "dashboard"))
    shutil.rmtree('dump/')
    print("finished syncing database")