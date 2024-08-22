import requests
import json

class OKTA:
    def __init__(self, url, key):
        self.url = url
        self.api_key = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': key
        }

    def get_groups(self):
        url = self.url + "/groups"
        return requests.get(url, headers=self.api_key)

    def get_group_detail(self, id):
        url = self.url + "/groups/" + id
        return requests.get(url, headers=self.api_key)
    
    def get_group_users(self, id):
        url = self.url + "/groups/" + id + "/users"
        return requests.get(url, headers=self.api_key)
    
    def get_user(self, email):
        url = self.url +"/users?q={}&limit=1".format(email)
        return requests.get(url, headers=self.api_key)

    def create_user(self, first, last, username, phone):
        url = self.url + "/users?activate=true"
        return requests.post(url, headers=self.api_key, data=json.dumps({"profile": {
            "firstName": first,
            "lastName": last,
            "email": username,
            "login": username,
            "mobilePhone": phone
        }}))

    def provision_user(self, group_id, user_id):
        url = self.url + "/groups/{}/users/{}".format(group_id, user_id)
        return requests.put(url, headers=self.api_key, data={})
    
    def deprovision_user(self, group_id, user_id):
        url = self.url + "/groups/{}/users/{}".format(group_id, user_id)
        return requests.delete(url, headers=self.api_key, data={})