from .conn import db
import requests
from datetime import datetime, timedelta

class Auvik:
    def __init__(self):
        dbcreds = db.accessList.find_one({"name": "Auvik api"})
        self.auth = (dbcreds["username"], dbcreds["apiKey"])
        self.base_url = "https://auvikapi.us2.my.auvik.com"
        self.headers = {
            "Content-Type":"application/json"
        }
        
    
    def get_tenant_list(self):
        client_list = []
        url = self.base_url+"/v1/tenants"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            for item in response.json()["data"]:
                if item["attributes"]["tenantType"] == "client":
                    client_list.append(item)
            return client_list
    
    
    def get_single_device_info(self, device_id):
        url = self.base_url+"/v1/inventory/device/info/{}".format(device_id)
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]
    
    
    def get_devices(self, after=None, deviceType=None):
        url = self.base_url+"/v1/inventory/device/info"
        params = {"page[first]":100}
        if after:
            params["page[after]"] = after
        if deviceType:
            params["filter[deviceType]"] = deviceType
        response = requests.get(url, params=params, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        
    def get_devices_url(self, url):
        res = requests.get(url, auth=self.auth)
        if res.status_code == 200:
            return res.json()
        
    def get_devices_details(self, tenants=None):
        url = self.base_url + "/v1/inventory/device/detail"
        devices = []
        res = requests.get(url, params={"page[first]": 1000, "tenants": ",".join(tenants)}, auth=self.auth)
        if res.status_code == 200:
            if len(res.json()["data"]) > 0:
                devices += res.json()["data"]
                while True:
                    if "next" in res.json()["links"].keys():
                        res = requests.get(res.json()["links"]["next"], auth=self.auth)
                        if res.status_code == 200:
                            if len(res.json()["data"]) > 0:
                                devices += res.json()["data"]
                            else:
                                break
                        else:
                            break
                    else:
                        break
        return devices
    
    def get_networks(self, after=None):
        url = self.base_url+"/v1/inventory/network/info"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        
        
    def get_networks_url(self, url):
        res = requests.get(url, auth=self.auth)
        if res.status_code == 200:
            return res.json()
        
    def get_network_details(self,):
        url = self.base_url+"/v1/inventory/network/info/{}".format(network_id)
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]

    def get_alert_details(self, alert_id):
        url = self.base_url+"/v1/alert/history/info/{}".format(alert_id)
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]
        
    
    def get_alerts(self, type):
        url = self.base_url+"/v1/alert/history/info"
        hours_ago = datetime.now() - timedelta(hours = 12)
        hours_ago = hours_ago.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        current = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        response = requests.get(url, params={"filter[severity]":type, "filter[status]":"created",  "filter[detectedTimeAfter]":hours_ago,"filter[detectedTimeBefore]":current, "page[first]":1000}, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]
        
    def get_device_warranties(self):
        url = self.base_url+"/v1/inventory/device/warranty"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]
        
    def get_device_lifecycles(self):
        url = self.base_url+"/v1/inventory/device/lifecycle"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]
        
    def get_entity_audit(self):
        url = self.base_url+"/v1/inventory/entity/audit"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()["data"]

    def get_device_details_extended(self, tenants=None):
        url = self.base_url + "/v1/inventory/device/detail/extended"
        devices = []
        # device_types = ["switch","l3Switch","router","accessPoint","firewall","workstation","server","storage","printer","copier","hypervisor","multimedia","phone","tablet","handheld","virtualAppliance","bridge","controller","hub","modem","ups","module","loadBalancer","camera","telecommunications","packetProcessor","chassis","airConditioner","virtualMachine","pdu","ipPhone","backhaul","internetOfThings","voipSwitch","stack","backupDevice","timeClock","lightingDevice","audioVisual","securityAppliance","utm","alarm","buildingManagement","ipmi","thinAccessPoint","thinClient"]
        device_types = ["workstation","server", "hypervisor"]
        for d in device_types:
            res = requests.get(url, params={"filter[deviceType]": d, "tenants": ",".join(tenants), "page[first]": 1000}, auth=self.auth)
            if res.status_code == 200:
                devices.extend(res.json()["data"])
        return devices