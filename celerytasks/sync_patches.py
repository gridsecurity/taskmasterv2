import paramiko
from scp import SCPClient
import os
import xmltodict
import xml.etree.ElementTree as ET
from datetime import datetime
from .conn import *
import re
import shutil

def sync_asset_patches():
    # download directory
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("gs-repo01.gridsecurity.io", username="gridsecadmin", key_filename="at_user_id_rsa")
    scp = SCPClient(ssh.get_transport())
    scp.get('patch_repo', recursive=True)
    # read repo folder
    site_folders = os.listdir('patch_repo')
    for s in site_folders:
        # list each site and get files
        # get site ID for assets
        site = db.sites.find_one({"site": s})
        patchable_assets = list(db.assets.find({"siteId": str(site["_id"]), "system.biosSerialNumber": {"$ne": ""}}))
        print(len(patchable_assets))
        patched_assets = []
        for f in os.listdir('patch_repo/' + s):
            # set up key and name
            if "_installed" in f:
                name = f.split("_installed")
                key = "installedPatches"
            elif "_pending" in f:
                name = f.split("_pending")
                key = "pendingPatches"
            else:
                continue
            # grab asset by serial number
            asset = db.assets.find_one({"system.biosSerialNumber": name[0]})
            if asset:
                # file path
                path = 'patch_repo/{}/{}'.format(s, f)
                patches = []
                if ".txt" in f:
                    # linux
                    text_file = open(path, "r")
                    for line in text_file.readlines():
                        if "Listing..." not in line:
                            split_line = line.split(" ")
                            patch = {
                                "ComputerName": asset["assetName"],
                                "KB": "",
                                "Title": split_line[0],
                                "Version": split_line[1],
                                "Architecture": split_line[2],
                                "text": line,
                                "Status": ""
                            }
                            if key == "pendingPatches":
                                try:
                                    currentVersion = re.search("\[(.*?)\]", line).group(1).split(": ")[1]
                                except:
                                    currentVersion = ""
                                patch["CurrentVersion"] = currentVersion
                            

                            patches.append(patch)
                    text_file.close()
                else:
                    # windows
                    tree = ET.parse(path)
                    xml_data = tree.getroot()
                    xmlstr = ET.tostring(xml_data, encoding='utf-8', method="xml")
                    data_dict = xmltodict.parse(xmlstr)

                    if data_dict["Objects"]:
                        if type(data_dict["Objects"]["Object"]) == dict:
                            patch_dict = {}
                            for prop in data_dict["Objects"]["Object"]["Property"]:
                                if prop["@Name"] == "Date":
                                    patch_dict[prop["@Name"]] = datetime.timestamp(datetime.strptime(prop["#text"], "%m/%d/%Y %H:%M:%S %p"))
                                else:
                                    patch_dict[prop["@Name"]] = prop["#text"] if "#text" in prop.keys() else ""
                            patches.append(patch_dict)
                        else:
                            for patch in data_dict["Objects"]["Object"]:
                                patch_dict = {}
                                for prop in patch["Property"]:
                                    if prop["@Name"] == "Date":
                                        patch_dict[prop["@Name"]] = datetime.timestamp(datetime.strptime(prop["#text"], "%m/%d/%Y %H:%M:%S %p"))
                                    else:
                                        patch_dict[prop["@Name"]] = prop["#text"] if "#text" in prop.keys() else ""
                                patches.append(patch_dict)
                db.assets.update_one({"_id": asset["_id"]}, {"$set": {key: patches}})
                patched_assets.append(asset)
                # remove from server
                
        # compare list
        patchable_ids = list(map(lambda x: x["_id"], patchable_assets))
        patched_ids = list(map(lambda x: x["_id"], patched_assets))
        missing_asset_ids = list(set(patchable_ids) - set(patched_ids))
        missing_assets = list(filter(lambda x: x["_id"] in missing_asset_ids, patchable_assets))
        asset_names = list(map(lambda x: x["assetName"], missing_assets))
        print(asset_names)
    # remove patch repo folder
    shutil.rmtree('patch_repo')