from .conn import db
import requests
import json

class NinjaOne:
    def __init__(self):
        dbcreds = db.accessList.find_one({"name": "NinjaOne api"})
        token_url = 'https://app.ninjarmm.com/oauth/token'
        token_data = {
            "grant_type": "client_credentials",
            'client_id': dbcreds["client-id"],
            'client_secret': dbcreds["client-secret"],
            'scope':'monitoring management',
        }
        token_r = requests.post(token_url, data=token_data)
        token = token_r.json().get('access_token')
        self.headers = {
            'Authorization': 'Bearer {}'.format(token),
            "Content-Type": "application/json",
            "Media-Type":"*/*"
        }
        
        self.base_url = "https://app.ninjarmm.com/"

    def schedule_maintenance(self, id, start: int, end: int):
        url = self.base_url + "/api/v2/device/{}/maintenance".format(id)
        body = json.dumps({
            "disabledFeatures": ["ALERTS"],
            "start": start,
            "end": end
        })
        return requests.put(url, data=body, headers=self.headers)
    
    def list_devices_detailed(self, device_filter=None, page_size=None, after=None):
        # returns a detailed list of all devices
        url = self.base_url+"api/v2/devices-detailed"
        response = requests.get(url, params={"df":device_filter, "pageSize":page_size, "after":after}, headers=self.headers)
        if response.status_code == 200:
            return response.json()
    
    def list_roles(self):
        url = self.base_url+"/api/v2/roles"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        
    def list_interfaces(self, id):
        url = self.base_url+"v2/device/{}/network-interfaces".format(id)
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        
    def list_patches(self, id, status):
        url = self.base_url+"v2/device/{}/os-patches".format(id)
        res = requests.get(url, params={"status":status}, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        
    def installed_patches(self, id):
        url = self.base_url+"v2/device/{}/os-patch-installs".format(id)
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
    def get_device_software_inventory(self, id):
        url = self.base_url+"v2/device/{}/software".format(id)
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
    def get_software_inventory(self):
        url = self.base_url+"v2/queries/software"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()

