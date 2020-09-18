#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python example script showing proper use of the Cisco Sample Code header.
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import meraki
import json
import logging
import pprint

import requests

from DETAILS import *

pp = pprint.PrettyPrinter(indent=2)
org_id = MERAKI_ORGANIZATION_ID
dashboard = meraki.DashboardAPI(MERAKI_API_KEY)

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Backup Function, add backup functions here
def backup(network_id):
    name = dashboard.networks.getNetwork(network_id)['name']
    data = {}
    print(f"Backing up {name} Network")

    print("Backing Up MX L7 Firewalls")
    data['mx_l7_firewall'] = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(network_id)

    print("Backing Up 1 to 1 NAT Rules")
    data['mx_1_1_nat_rules'] = dashboard.appliance.getNetworkApplianceFirewallOneToOneNatRules(network_id)

    print("Backing Up Wireless Settings")
    data['wireless_settings'] = dashboard.wireless.getNetworkWirelessSettings(network_id)

    print("Backing Up SSIDs")
    data['ssids'] = dashboard.wireless.getNetworkWirelessSsids(network_id)
    pp.pprint(data['ssids'])

    print("Backing Up Malware Settings")
    try:
        data['malware_settings'] = dashboard.appliance.getNetworkApplianceSecurityMalware(network_id)
    except:
        print("AMP is not Supported")

    print("Backing Up Switch Port Schedules")
    data['switch_port_schedules'] = dashboard.switch.getNetworkSwitchPortSchedules(network_id)

    print("Backing Up Switch ACLs")
    data['switch_acls'] = dashboard.switch.getNetworkSwitchAccessControlLists(network_id)
    new = [item for item in data['switch_acls']['rules'] if not item["comment"] == 'Default rule']
    data['switch_acls'] = new

    with open(f'configs/{name}.json', 'w+') as outfile:
        json.dump(data, outfile, indent=4)

    print("Backup Complete!")


# Backup Function, add restore functions here
def restore(network_id, filename):
    name = dashboard.networks.getNetwork(network_id)['name']
    data = {}
    print(f"Restoring {name} Network from {filename}.json")
    networklist = {}
    idlist = {}
    data = {}

    with open(f'configs/{filename}', 'r') as infile:
        data = json.load(infile)

        print("Restoring MX L7 Firewalls")
        body = data['mx_l7_firewall']['rules']
        response = dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules(network_id, rules=body)

        print("Restoring 1 to 1 NAT Rules")
        body = data['mx_1_1_nat_rules']['rules']
        response = dashboard.appliance.updateNetworkApplianceFirewallOneToOneNatRules(network_id, rules=body)

        print("Restoring Wireless Settings")
        body = data['wireless_settings']
        url = f"https://api.meraki.com/api/v0/networks/{network_id}/wireless/settings"
        payload = json.dumps(body)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Cisco-Meraki-API-Key": MERAKI_API_KEY
        }
        response = requests.request('PUT', url, headers=headers, data=payload)

        print("Restoring SSIDs")
        body = data['ssids']
        for ssid in body:
            if 'Unconfigured SSID' in ssid['name']:
                continue
            else:
                number = str(ssid['number'])
                ssid.pop('number')
                url = f"https://api.meraki.com/api/v0/networks/{network_id}/ssids/{number}"
                payload = json.dumps(ssid)
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY
                }
                response = requests.request('PUT', url, headers=headers, data=payload)
                print(f"Restored {ssid['name']}")

        print("Restoring Malware Settings")
        try:
            body = data['malware_settings']
            response = dashboard.appliance.updateNetworkApplianceSecurityMalware(network_id, **body)
        except:
            print("AMP is not supported")

        print("Restoring Switch Port Schedules")
        body = data['switch_port_schedules']
        try:
            for schedule in body:
                id = schedule['id']
                name = schedule['name']
                portSchedule = schedule['portSchedule']
                response = dashboard.switch.updateNetworkSwitchPortSchedule(network_id, name=name,
                                                                                           portSchedule=portSchedule,
                                                                                           portScheduleId=id)
        except:
            for schedule in body:
                try:
                    id = schedule['id']
                    name = schedule['name']
                    portSchedule = schedule['portSchedule']
                    response = dashboard.switch.createNetworkSwitchPortSchedule(network_id,
                                                                                            name=name,
                                                                                            portSchedule=portSchedule)
                except:
                    i = 1
                    while (1):
                        try:
                            id = schedule['id']
                            name = schedule['name'] + str(i)
                            portSchedule = schedule['portSchedule']
                            response = dashboard.switch.createNetworkSwitchPortSchedule(network_id,
                                                                                                       name=name,
                                                                                                       portSchedule= \
                                                                                                           portSchedule)
                            break
                        except:
                            i += 1

        print("Restoring Switch ACLs")
        body = data['switch_acls']
        response = dashboard.switch.updateNetworkSwitchAccessControlLists(network_id, rules=body)
        print("Restore Complete!")
