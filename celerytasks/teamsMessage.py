from .conn import db
import pymsteams

class Teams:
    def __init__(self, group):
        group = db.group_provisions.find_one({"groupName": group})
        if group:
            self.url = group["teamsURL"]
        else:
            raise "Error"
        
    
    def send_message(self, message):
        teams = pymsteams.connectorcard(self.url)
        teams.text(message)
        teams.send()
