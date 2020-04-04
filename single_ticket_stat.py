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
jql_string_R5 = 'project = CCP AND fixVersion in ("Release 5.0") ORDER BY type DESC,  key ASC'

ticket_list_file = 'ticket_list.csv'
ticket_history_file = 'ticket_history.csv'
ticket_header = ['Issue key', 'Type', 'Summary', 'Status', 'Release', 'Story Point', 'Last Sprint']
ticket_raw = []
history_header = ['Issue key', 'Author', 'Timestamp', 'Item type', 'From', 'To']
history_raw = []

def run_JQL_query(query_string):
    issues_in_proj = jira.search_issues(query_string)
    for issue in issues_in_proj:
        print('{}: {}'.format(issue.key, issue.fields.summary))
        type_name = issue.fields.issuetype.name
        summary = issue.fields.summary
        status = issue.fields.status.name
        version_name = issue.fields.fixVersions[0].name
        story_point = issue.fields.customfield_10105
        last_sprint = str(re.findall(r"name=[^,]*", issue.fields.customfield_10103[0]))
        last_sprint = last_sprint.split("=")[1]
        last_sprint = last_sprint.split("'")[0]
        ticket_item = [issue.key, type_name, summary, status, version_name, story_point, last_sprint]
        ticket_raw.append(ticket_item)
    with open(ticket_list_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(ticket_header)
        for item in ticket_raw:
            csv_file.writerow(item)
    return issues_in_proj

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




for history in issue.changelog.histories:
    for item in history.items:
        if item.field == 'status' or item.field == 'assignee':
            created_ts = datetime.strptime(str(history.created), '%Y-%m-%dT%H:%M:%S.%f%z')
            created_ts = datetime.strftime(created_ts, '%Y-%m-%d %H:%M:%S')
            history_item = [key, history.author.displayName, created_ts, item.field, item.fromString, item.toString]
            history_raw.append(history_item)
            #print(key, ';', history.author.displayName, ';', created_ts, ';', item.field, ';', item.fromString, ';', item.toString)

history_raw = sorted(history_raw, key=lambda l:l[2])

csv_file_name = key + '_history.csv'
with open(csv_file_name, mode='w', newline='', encoding='utf-8') as csv_file:
    csv_file = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_file.writerow(history_header)
    for item in history_raw:
        csv_file.writerow(item)

run_JQL_query(jql_string_R5)
