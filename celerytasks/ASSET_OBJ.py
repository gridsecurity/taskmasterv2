networkObj = {
        'id' : "",
        'siteId' : "",
        'attributes' : {
            'networkName' : "",
            'networkType' : "",
            'description' : "",
            'scanStatus' : "",
            'lastModified' : ''
        },
        'devices' : [],
        'lastUpdateByUser' : "" # Last time the object was updated
    }

asset = { # empty asset object to build off of, prevents keyerrors going forward
        'id' : "",
        'siteId' : "",
        'serviceTag' : "",
        'vmGuest' : "",
        'vmHost' : "",
        'vmOS' : "",
        'assetName' : "",
        'dnsName' : "",
        'deviceType' : "",
        'nodeRoleId' : "",
        'nodeRoleName' : "",
        'nodeRoleDesc' : "",
        'nodeClass' : "",
        'auvikId' : "",
        'ninjaId' : '',
        'indDefId' : "",
        'netSheetId' : "",
        'natIp' : "",
        'ipAddresses' : [],
        'publicIP' : '',
        'interfaces' : [],
        'networks': [],
        'locationId' : 0,
        'parentDeviceId' : "",
        'manual' : False,
        'os' : {
            'manufacturer' : "",
            'name' : "",
            'architecture' : "",
            'lastBootTime' : 0,
            'buildNumber' : "",
            'releaseId' : "",
            'servicePackMajorVersion' : 0,
            'servicePackMinorVersion': 0,
            'locale' : "",
            'language' : "",
            'needsReboot' : False
        },
        'processors' : [],
        'system' : {
            'name' : "",
            'manufacture' : "",
            'model' : "",
            'biosSerialNumber' : "",
            'serialNumber' : "",
            'domain' : "",
            'domainRole' : "",
            'numberOfProcessors' : 0,
            'totalPhysicalMemory' : 0,
            'virtualMachine' : False,
            'chassisType' : ""
        },
        'volumes' : [],
        'pendingPatches' : [],
        'approvedPatches' : [],
        'rejectedPatches' : [],
        'installedPatches' : [],
        'offline' : True,
        'lastLoggedInUser' : "",
        'lastContact' : "",
        'lastUpdate' : "", # Last time the object was updated by Ninja
        'lastModified' : "", # Last time the object was updated by Auvik
        'lastUpdateByUser' : "" # Last time the object was updated
}