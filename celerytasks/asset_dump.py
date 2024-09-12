import re
import time
from .ninja_one import NinjaOne
from .auvik import Auvik
from .conn import db, network
from bson import ObjectId
from datetime import datetime
from copy import deepcopy
import pymsteams
from .ASSET_OBJ import networkObj, asset

def dump_assets():
    # Nightly pull of ninja one assets
    ninja = NinjaOne()
    roles = ninja.list_roles()
    # set roles
    for r in roles: 
        db.device_roles.update_one({"id": r["id"]}, {"$set": r}, upsert=True)
    # get sites
    sites = list(db.sites.find({}))

    def pull_id():
        for s in sites:
            if s["id_locations"]:
                for id_asset in list(db.id_assets.find({"location": s["id_locations"], "exists": True})):
                    # try to find id asset by indDefId
                    asset = db.assets.find_one({"siteId": str(s["_id"]), "indDefId": str(id_asset["assetUuid"])})
                    interfaces = []
                    if asset:
                        print("found asset")
                    else:
                        if "interfaces" in id_asset.keys():
                            for ip in id_asset["interfaces"]:
                                interfaces.append(ip["interfaceIPAddress"])
                                # set asset to none and try to find one in database
                                asset = None
                                if ip["interfaceIPAddress"]:
                                    asset = db.assets.find_one({"$or": [
                                        {"siteId": str(s["_id"]), "assetName": {"$regex": id_asset["assetName"], "$options": "i"}, "deviceType": {"$ne": "VMGuest"}},
                                        {"SiteId": str(s["_id"]), "ipAddresses": ip["interfaceIPAddress"], "deviceType": {"$ne": "VMGuest"}}
                                    ]})
                                    if asset:
                                        print("found asset")
                    # found asset to update
                    if asset:
                        db.assets.update_one({"indDefId": str(id_asset["assetUuid"])}, {"$set": {"assetName": id_asset["assetName"], "indDefUpdated": datetime.timestamp(datetime.today())}})
                    # set up new object to insert
                    else:
                        new_asset = deepcopy(asset)
                        new_asset["assetName"] = id_asset["assetName"]
                        new_asset["ipAddresses"] = list(set(interfaces))
                        new_asset["indDefId"] = str(id_asset["assetUuid"])
                        new_asset["siteId"] = str(s["_id"])
                        new_asset["updated"] = datetime.timestamp(datetime.today())
                        new_asset["indDefUpdated"] = datetime.timestamp(datetime.today())
                        db.assets.insert_one(new_asset)

    def process_networkSheet():
        print( "Processing Network Sheet Objects")
        start = time.time()
        for s in sites:
            print(s["site"])
            for sheet in s["networkSheets"]:
                # get site template
                template = network.sitetemplate.find_one({"_id": ObjectId(sheet)})
                if template:
                    # get items
                    for i in list(network.items.find({"site": template["site"]})):
                        print(i)
                        a = db.assets.find_one({
                            "siteId": str(s["_id"]),
                            "$or": [
                                {"ipAddresses": i["ipv4"].split("/")[0]},
                                {"netSheetId": str(i["_id"])}
                            ]
                        })
                        a = a if a else deepcopy(asset)
                        if not a['ipAddresses']:
                            a['ipAddresses'].append(i["ipv4"].split("/")[0])
                        a['netSheetId'] = str(i['_id'])
                        a["siteId"] = str(s["_id"])
                        a['assetName'] = i['assetId'] if a['assetName'] == 'Device@{}'.format(a['ipAddresses'][0]) else a['assetName']
                        a['natIp'] = i['gridsec_nat'] if a['natIp'] == '' else a['natIp']
                        a['deviceType'] = i['device_type'] if a['deviceType'] == '' else a['deviceType']
                        a['assetName'] = i['assetId'] if a['assetName'] == '' else a['assetName']
                        a['system']['model'] = i['make_model'] if a['system']['model'] == '' else a['system']['model']
                        a['system']['serialNumber'] = i['serial'] if a['system']['serialNumber'] == '' else a['system']['serialNumber']
                        db.assets.update_one({"_id": a["_id"]}, {"$set": a}) if '_id' in a.keys() else db.assets.update_one({"netSheetId": a["netSheetId"]}, {"$set": a}, upsert=True)

        finish = time.time()
        difference = (finish - start ) / 60
        print( "Completed Network Sheet Objects")
        print(difference)


    def process_ninja():
        print( "Processing NinjaOne Objects")
        start = time.time()
        def ninjaToAssetSync():
            print( "Syncing NinjaOne Assets")
            for d in list(db.ninja.find({"exists": True})):
                site = next(filter(lambda x: x['ninjaLocation'] == str( d['locationId'] ), sites), None)
                siteId = str(site['_id']) if site else ""

                a = db.assets.find_one({'ninjaId':d['id']}) # See if we already have the asset in the DB # See if we already have the asset in the DB
                upsert = True
                if a:
                    upsert = False
                else:
                    try:
                        a = a if a else db.assets.find_one({ '$and' : [ {'siteId' : siteId}, {'ipAddresses' : d['ipAddresses']}, {'ninjaId' : ""} ] })
                    except:
                        pass
                a = a if a else deepcopy(asset) # create a new asset if one wasn't found

                # Build out a new asset
                if not a['ninjaId']:
                    a['ninjaId'] = d['id']
                    a['assetName'] = d["systemName"] if "systemName" in d.keys() else d["dnsName"] if "dnsName" in d.keys() else d["netbiosName"] if "netbiosName" in d.keys() else ""
                    a['assetName'] = a['assetName'].split(".")[0]
                    if not site:
                        print( d['locationId'], a['assetName'] )
                    a['siteId'] = siteId

                for k, v in d.items(): # Match all the keys possible
                    if k == '_id':
                        continue
                    if k in a.keys(): # Does the key match back
                        if isinstance(v, dict): # Sub object, need to iterate through this as well.
                            for key, value in v.items(): # Only going one step deep
                                a[k][key] = value
                                continue
                        else:
                            a[k] = v


                # Update Role details -- We pull them seperate but combine in the asset
                role = next(filter(lambda x: x['id'] == d['nodeRoleId'], roles), None)
                a['nodeRoleName'] = role['name'] if 'name' in role.keys() else ""
                a['nodeRoleDesc'] = role['description'] if 'description' in role.keys() else ""

                # Pull all the interface details and update ipAddress list with valid IP's only.
                a["interfaces"] = ninja.list_interfaces(a["ninjaId"])
                if a["interfaces"]:
                    a['ipAddresses'] = [] # Clear out the IP's if we have the interfaces. Resets the IP list to what is matched.
                    for i in a["interfaces"]:
                        i['apipa'] = False
                        if any("169.254" in ip for ip in i['ipAddress']):
                            i['apipa'] = True
                            continue
                        if len(i['ipAddress']) >= 1:
                            if any( i['ipAddress'][0] in ip for ip in a['ipAddresses']):
                                continue
                            a['ipAddresses'].append(i['ipAddress'][0])

                #return all patch detail
                a['pendingPatches'] = ninja.list_patches(a['ninjaId'], "MANUAL")
                a['pendingPatches'] = a['pendingPatches'] if a['pendingPatches'] else []

                a['approvedPatches'] = ninja.list_patches(a['ninjaId'], "APPROVED")
                a['approvedPatches'] = a['approvedPatches'] if a['approvedPatches'] else []

                a['rejectedPatches'] = ninja.list_patches(a['ninjaId'], "REJECTED")
                a['rejectedPatches'] = a['rejectedPatches'] if a['rejectedPatches'] else []

                a['installedPatches'] = ninja.installed_patches(a['ninjaId'])
                a['installedPatches'] = a['installedPatches'] if a['installedPatches'] else []

                # Final updates and push to DB
                a["lastUpdateByUser"] = datetime.timestamp(datetime.today())
                db.assets.update_one({"_id": a["_id"]}, {"$set": a}) if '_id' in a.keys() else db.assets.update_one({ 'ninjaId' : int( a['ninjaId'] )}, {"$set" : a}, upsert=upsert)
        
        
        def vmToAssetSync():
            print( "Syncing vmGuests to Hosts and Asset's")
            for v in list(db.assets.find({'deviceType' : "VMGuest"})):
                vmHost = str(db.assets.find_one({'ninjaId': v['parentDeviceId'] })['_id'])
                vmOS = db.assets.find_one({ '$and' : [ {'deviceType' : 'AgentDevice'}, {'assetName' : re.compile(v['assetName'], re.IGNORECASE)}, {'siteId' : v['siteId'] } ] })
                if vmOS and vmOS['ipAddresses'] != []:
                    vmOS = vmOS if vmOS else db.assets.find_one({ '$and' : [ {'deviceType' : 'AgentDevice'}, {'ipAddresses': {'$in' : [ v['ipAddresses'][0]] } }, {'siteId' : v['siteId'] } ] })
                vmOS = str(vmOS['_id']) if vmOS else ""
                if vmOS:
                    db.assets.update_one({ '_id' : ObjectId(vmOS)}, {'$set' : {'vmGuest' : str(v['_id'])}} )
                db.assets.update_one({'_id' : v['_id']}, {'$set' : {'vmHost' : vmHost, 'vmOS' : vmOS}})
            
        ninjaToAssetSync()
        vmToAssetSync()

        finish = time.time()
        difference = (finish - start ) / 60
        print( "Completed NinjaOne Objects")
        print(difference)

    def process_auvik():
        print( "Processing Auvik Objects" )
        start = time.time()
        for d in list(db.auvik.find({"exists": True})):
            print(d["id"])
            site = next(filter(lambda x: x['auvikTenant'] == d['relationships']['tenant']['data']['id'], sites), None)
            siteId = str(site['_id']) if site else ""
            a = db.assets.find_one({'auvikId' : d['id']}) # See if we already have the asset in the DB
            # set upsert
            upsert = True
            if a:
                upsert = False
            a = a if a else db.assets.find_one({ '$and' : [ {'siteId' : siteId}, {'dnsName' : d['attributes']['deviceName']}] })
            a = a if a else db.assets.find_one({ '$and' : [ {'siteId' : siteId}, {'ipAddresses' : d['attributes']['ipAddresses']}] })
            a = a if a else deepcopy(asset)

            # Default updates from Auvik linking the asset to the auvik object
            a['auvikId'] = d['id']
            a['offline'] = False if d['attributes']['onlineStatus'] == 'online' else True
            a['lastModified'] = d['attributes']['lastModified'] # Auviks last modified timestamp

            # Check to see if we have the network's details
            a['networks'] = d['relationships']['networks']['data']

            # Check to make sure these haven't been populated by Ninja First
            a['siteId'] = siteId if not a['siteId'] else a['siteId']
            a['ipAddresses'] = d['attributes']['ipAddresses'] if a['ipAddresses'] == [] else a['ipAddresses']
            a['assetName'] = d['attributes']['deviceName'] if a['assetName'] == "" else a['assetName']
            a['deviceType'] = d['attributes']['deviceType'] if not a['deviceType'] else a['deviceType']
            if '@' in d['attributes']['deviceName']:
                a['deviceType'] = "unknown" if not a['deviceType'] else a['deviceType']
            a["lastUpdateByUser"] = datetime.timestamp(datetime.today()) # Portals last modified timestamp
            db.assets.update_one({"_id": a["_id"]}, {"$set": a}) if '_id' in a.keys() else db.assets.update_one({"auvikId": d["id"]}, {"$set": a}, upsert=upsert)
        
        
        finish = time.time()
        difference = (finish - start ) / 60
        print( "Completed Auvik Objects")
        print(difference)

    
    process_ninja()
    process_auvik()
    pull_id()
    # process_networkSheet()

    request_url = 'https://gridsec.webhook.office.com/webhookb2/765cfca8-8ff7-42a5-b455-50802ac57775@9542b69d-0d8b-4244-8f4f-debecdbdc2b5/IncomingWebhook/c68585d562194ba4841985d656f11986/096bc56c-47ed-4dce-a63a-5bb9c1a57a08'
    messageTeams = pymsteams.connectorcard(request_url)
    messageTeams.text('Finished Processing Asset Dump')
    messageTeams.send()
