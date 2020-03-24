# library modules
import sys, os, traceback, argparse
from datetime import datetime
from datetime import timedelta
import time
import re
import ast
import csv

from jira import JIRA
import pandas as pd
import numpy as np
import logging
import json

import jira_credentials
jira_user = jira_credentials.login['jira_user']
jira_apikey = jira_credentials.login['jira_apikey']

jira_server = 'https://bmigroup.atlassian.net'

options = {
 'server': jira_server
}

jira = JIRA(options, basic_auth=(jira_user,jira_apikey) )

ticket = 'CCP-1258'
issue = jira.issue(ticket, expand='changelog')
key = issue.key
type_name = issue.fields.issuetype.name
summary = issue.fields.summary
status = issue.fields.status.name
version_name = issue.fields.fixVersions[0].name
story_point = issue.fields.customfield_10105
last_sprint = str(re.findall(r"name=[^,]*", issue.fields.customfield_10103[0]))
last_sprint = last_sprint.split("=")[1]
last_sprint = last_sprint.split("'")[0]
single_ticket = [key, type_name, summary, status, version_name, story_point, last_sprint]
#print(key, ';', type_name, ';', summary, ';', status, ';', version_name, ';', story_point, ';', last_sprint)
print(single_ticket)

history_header = ['Issue key', 'Author', 'Timestamp', 'Item type', 'From', 'To']
raw_history = []

for history in issue.changelog.histories:
    for item in history.items:
        if item.field == 'status' or item.field == 'assignee':
            created_ts = datetime.strptime(str(history.created), '%Y-%m-%dT%H:%M:%S.%f%z')
            created_ts = datetime.strftime(created_ts, '%Y-%m-%d %H:%M:%S')
            history_item = [key, history.author.displayName, created_ts, item.field, item.fromString, item.toString]
            raw_history.append(history_item)
            #print(key, ';', history.author.displayName, ';', created_ts, ';', item.field, ';', item.fromString, ';', item.toString)

raw_history = sorted(raw_history, key=lambda l:l[2])

csv_file_name = key + '_history.csv'
with open(csv_file_name, mode='w', newline='', encoding='utf-8') as csv_file:
    csv_file = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_file.writerow(history_header)
    for item in raw_history:
        csv_file.writerow(item)