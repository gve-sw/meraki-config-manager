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


from flask import render_template, request
from app import app
import backup as bk
import logging
import pprint
import meraki
import os


pp = pprint.PrettyPrinter(indent=2)
org_id = app.config['MERAKI_ORGANIZATION_ID']
dashboard = meraki.DashboardAPI(api_key=app.config['MERAKI_API_KEY'], suppress_logging=True)

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Mode Selection
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', title='Home')


# Backup Mode
@app.route('/backup', methods=['GET', 'POST'])
def backup():
    networklist = []
    namelist =[]
    n = 0
    for network in dashboard.organizations.getOrganizationNetworks(org_id):
        networklist.append(network)
        n += 1
    if request.method == 'GET':
        return render_template('backup.html', title='Backup', tab=1, netdata=networklist, status="Waiting for job")
    elif request.method == 'POST':
        netslist = request.form.getlist('nets')
        for network in netslist:
            bk.backup(network)
        for network in netslist:
            namelist.append(dashboard.networks.getNetwork(network)['name'])
        return render_template('backup.html', title='Backup', tab=1, netdata=networklist, status="Finished Backup",
                               netslist=namelist)


# Restore Mode
@app.route('/restore', methods=['GET', 'POST'])
def restore():
    networklist = []
    namelist = []
    backuplist = []
    for name in os.listdir('configs/'):
        if name.endswith('.json'):
            backuplist.append(name)
    n = 0
    for network in dashboard.organizations.getOrganizationNetworks(org_id):
        networklist.append(network)
        n += 1
    if request.method == 'GET':
        return render_template('restore.html', title='Restore', tab=1, netdata=networklist, status="Waiting for job",
                               backuplist=backuplist)
    elif request.method == 'POST':
        netslist = request.form.getlist('nets')
        backupfile = request.form.get('backups')
        for network in netslist:
            bk.restore(network, backupfile)
        for network in netslist:
            namelist.append(dashboard.networks.getNetwork(network)['name'])
        return render_template('restore.html', title='Restore', tab=1, netdata=networklist, status="Finished Restore",
                               netslist=namelist, backuplist=backuplist)
