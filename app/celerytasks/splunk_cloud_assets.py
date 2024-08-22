from .conn import db
from bson import ObjectId
import json

def splunk_cloud_assets_push():
    # searchSplunkCound()
    token = "eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJjZ2FsbGFnaGVyQGdyaWRzZWMuY29tIGZyb20gc2gtaS0wOTFlMDUyOTYxMzBmYTc0MiIsInN1YiI6ImNnYWxsYWdoZXJAZ3JpZHNlYy5jb20iLCJhdWQiOiJwb3J0YWwgYXNzZXRzIGxpc3QiLCJpZHAiOiJTcGx1bmsiLCJqdGkiOiIxNGJhNjg2N2FlNzA5YWYxOWQzZGQzNTkyNTM0MGFiZWZmNWE0MTU2YTYzZGE2YzNiZDViYzE1NTQyZTI5NGZkIiwiaWF0IjoxNzE0MDc1NjE3LCJleHAiOjE3MTY2Njc2MTcsIm5iciI6MTcxNDA3NTYxN30.c07DOljfI2qLluC0up2DnejIMcVzz90UdxemXwyhCzoWeylEh17FhwA6Qhy0WzyaczHNMJq6qkTv-JSYce3jGg"
    assets = list(db.assets.find({}))
    # get location for sites
    # sites = list(db.sites.find({}, {"site": 1, "longitude": 1, "latitude": 1, "_id": 1}))
    # ninja_assets = list(db.ninja_one_assets.find({}))
    # ninja = NinjaOne()
    # ninja_roles = ninja.list_device_roles()
    roles = db.accessList.find_one({"name": "Ninja Device Roles"})["roles"]
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
        # reverse_geocode = gmaps.reverse_geocode((a["lat"], a["long"]))
        # if "ninjaId" in a.keys():
        #     ninja_asset = list(filter(lambda x: x["id"] == a["ninjaId"], ninja_assets))[0]
        #     a["mac"] = ninja_asset["macAddresses"] if "macAddresses" in ninja_asset.keys() else []
        #     a["nt_host"] = ninja_asset["systemName"] if "systemName" in ninja_asset.keys() else ""
        #     a["dns"] = ninja_asset["dnsName"] if "dnsName" in ninja_asset.keys() else ""
        #     role = list(filter(lambda x: x["id"] == ninja_asset["nodeRoleId"], ninja_roles))[0]
        #     if role["custom"] == False:
        #         a["priority"] = "medium"
        #     else:
        #         r = list(filter(lambda x: x["id"] == role["id"], roles))
        #         if len(r) > 0:
        #             a["priority"] = r[0]["priority"]
        #     a["category"] = role["name"]
        #     try:
        #         a["vendor"] = ninja_asset["vendor"] if "vendor" in ninja_asset.keys() else ninja_asset["os"]["manufacturer"] if "os" in ninja_asset.keys() else ""
        #     except:
        #         a["vendor"] = ""
        #     a["os_type"] = ninja_asset["nodeClass"]
        #     if role["name"] != "GC-WKS":
        #         a["is_expected"] = True
        #         a["should_timesync"] = True
        #     else:
        #         a["is_expected"] = False
        #         a["should_timesync"] = False
        # # set asset as event
        event_list.append({"event": a, "index": "asset_inventory_customers", "sourcetype": "_json"})
    json_objects = json.dumps(assets, indent=4)
    with open('asset.json', "w") as outfile:
        outfile.write(json_objects)
    # chunk_size = 10
    # while event_list:
    #     chunk, event_list = event_list[:chunk_size], event_list[chunk_size:]
    #     # join together as string
    #     str_chunk =  "\n".join(list(map(lambda x: str(x).replace("\'", "\""), chunk)))
    #     res = requests.post('https://http-inputs-gridsec.splunkcloud.com/services/collector/raw', headers={"Authorization": "Splunk {}".format(token)}, data=str_chunk)
    #     print(res.text)
    
    # site_token = "865ab259-1a96-43e0-b1a5-f7e1f1736d15"
    # df = pd.DataFrame.from_records(sites)
    # df.to_csv("sites.csv")
    # for s in sites:
    #     s["id"] = str(s.pop("_id"))
    #     print(s["site"])
    #     try:
    #         s.pop("modifiedDate")
    #     except:
    #         pass
    #     try:
    #         s.pop("creationDate")
    #     except:
    #         pass
    #     try:
    #         s["latitude"] = str(s["latitude"])
    #         s["longitude"] = str(s["longitude"])
    #     except:
    #         pass
    #     payload = {
    #         "index": "asset_location_customers",
    #         "event": s,
    #         "sourcetype": "site"
    #     }
    #     res = requests.post('https://http-inputs-gridsec.splunkcloud.com/services/collector', headers={"Authorization": "Splunk {}".format(site_token)}, data=json.dumps(payload))
    #     print(res.text)
