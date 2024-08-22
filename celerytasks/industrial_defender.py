import requests
from .conn import db 
from django.http import Http404

class Industrial_Defender:
    def __init__(self):
        dbcreds = db.accessList.find_one({"name": "Industrial Defender API"})
        token_url = 'https://gs-asm01/AsmDataService/connect/token'
        token_data = {
            "grant_type": "client_credentials",
            'client_id': dbcreds["clientId"],
            'client_secret': dbcreds["clientSecret"],
        }
        token_r = requests.post(token_url, data=token_data, verify=False)
        token = token_r.json().get('access_token')
        self.headers = {
            'Authorization': 'Bearer {}'.format(token),
            "Content-Type": "application/json"
        }
        
        self.base_url = "https://gs-asm01/AsmDataService"
        
        
        
    def get_admin_props(self):
        url = self.base_url + "/api/admin-properties"
        response = requests.get(url, headers=self.headers, verify=False)
        print(response)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Http404("Couldnt get locations")
        
    def get_assets_with_details_from_location(self, location, asset_count):
        assets = []
        limit = 100
        url = self.base_url + "/api/assets/details"
        response = requests.get(url, params={"location":location, "limit":limit}, headers=self.headers, verify=False)
        if response.status_code == 200:
            assets += response.json()["data"]
            if asset_count <=limit:
                return assets
            else:
                page = 2
                assets_remaining = asset_count - limit
                while assets_remaining != 0:
                    if assets_remaining < limit:
                        response = requests.get(url, params={"location":location, "page":page, "limit":assets_remaining}, headers=self.headers, verify=False)
                        assets += response.json()["data"]
                        break
                    else:
                        response = requests.get(url, params={"location":location, "page":page, "limit":limit}, headers=self.headers, verify=False)
                        assets += response.json()["data"]
                        page += 1
                        assets_remaining -= limit
        return assets
    
    
    
    
    def get_location_asset_count(self, location):
        url = self.base_url + "/api/assets/count/total"
        response = requests.get(url, params={"location":location}, headers=self.headers, verify=False)
        if response.status_code == 200:
            return response.json()["data"]["counter"]["assetsCounter"]
        

    
    def get_os_groups(self):
        url = self.base_url + "/api/asset-groups"
        response = requests.get(url, headers=self.headers, verify=False)
        if response.status_code == 200:
            return response.json()["data"]
    
    def get_state_data_for_assets(self, location, asset_count):
        assets = []
        limit = 100
        url = self.base_url + "/api/state/actual"
        response = requests.get(url, params={"location":location,"limit":limit}, headers=self.headers, verify=False)
        if response.status_code == 200:
            assets += response.json()["data"]
            if asset_count <=limit:
                return assets
            else:
                page = 2
                assets_remaining = asset_count - limit
                while assets_remaining != 0:
                    if assets_remaining < limit:
                        response = requests.get(url, params={"location":location, "page":page, "limit":assets_remaining}, headers=self.headers, verify=False)
                        assets += response.json()["data"]
                        break
                    else:
                        response = requests.get(url, params={"location":location, "page":page, "limit":limit}, headers=self.headers, verify=False)
                        assets += response.json()["data"]
                        page += 1
                        assets_remaining -= limit
        return assets