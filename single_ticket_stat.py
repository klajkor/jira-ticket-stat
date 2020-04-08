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

start_time = time.time()

jira_user = jira_credentials.login['jira_user']
jira_apikey = jira_credentials.login['jira_apikey']
jira_server = 'https://bmigroup.atlassian.net'
options = {
 'server': jira_server
}
jql_string_R5 = 'project = CCP AND fixVersion in ("Release 5.0") ORDER BY type DESC,  key ASC'
jql_string_R6 = 'project = CCP AND fixVersion in ("Release 6.0") ORDER BY type DESC,  key ASC'
jql_string_all_epics = 'project = CCP AND type in (Epic) ORDER BY KEY ASC'
jql_string_sprint = 'issueKey in (CCP-443,CCP-628,CCP-640,CCP-1431,CCP-1543,CCP-1571,CCP-1580,CCP-1582,CCP-1617,CCP-1625)'

ticket_list_file = 'ticket_list.csv'
ticket_history_file = 'ticket_history.csv'
ticket_header = ['Issue key', 'Type', 'Summary', 'Status', 'Release', 'Story Point', 'First Sprint', 'Last Sprint', 'Created', 'Updated', 'Epic Key', 'Epic Title', 'Labels']
ticket_raw = []
history_header = ['Issue key', 'Issue ID', 'Author', 'Timestamp', 'Item type', 'From', 'To']
history_raw = []
all_epics = {}
issues_in_proj = {}

def get_all_epics(query_string):
    tmp_dict = {}
    issues_in_proj = jira.search_issues(query_string, maxResults=200)
    for issue in issues_in_proj:
        tmp_dict[issue.key] = issue.fields.summary
    return tmp_dict


def run_JQL_query(query_string):
    issues_in_query = jira.search_issues(query_string, maxResults=1000)
    for issue in issues_in_query:
        type_name = issue.fields.issuetype.name
        summary = issue.fields.summary
        status = issue.fields.status.name
        version_name = ''
        if type(issue.fields.fixVersions) is list and len(issue.fields.fixVersions) > 0:
            version_name = issue.fields.fixVersions[0].name
        story_point = issue.fields.customfield_10105
        if type(story_point) is float:
            story_point = int(story_point)
        first_sprint = ''
        last_sprint = ''
        sprints = issue.fields.customfield_10103
        if type(sprints) is list:
            sprint_names = []
            for sprint in sprints:
                sprint_name = str(re.findall(r"name=[^,]*", sprint))
                sprint_name = sprint_name.split("=")[1]
                sprint_name = sprint_name.split("'")[0]
                sprint_names.append(sprint_name)
            sprint_names = sorted(sprint_names, key=lambda x: x[0])
            first_sprint = sprint_names[0]
            last_sprint = sprint_names[-1]
        issue_created_ts = datetime.strptime(str(issue.fields.created), '%Y-%m-%dT%H:%M:%S.%f%z')
        issue_created_ts = datetime.strftime(issue_created_ts, '%Y-%m-%d %H:%M:%S')
        issue_updated_ts = datetime.strptime(str(issue.fields.updated), '%Y-%m-%dT%H:%M:%S.%f%z')
        issue_updated_ts = datetime.strftime(issue_updated_ts, '%Y-%m-%d %H:%M:%S')
        epic_link = issue.fields.customfield_10006
        epic_link_title = ""
        if type(epic_link) is str:
            epic_link_title = all_epics.get(epic_link)
        all_labels = []
        labels = issue.fields.labels
        for i in labels:
            all_labels.append(i)
        ticket_item = [issue.key, type_name, summary, status, version_name, story_point, first_sprint, last_sprint, issue_created_ts, issue_updated_ts, epic_link, epic_link_title, all_labels]
        ticket_raw.append(ticket_item)
    with open(ticket_list_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(ticket_header)
        for item in ticket_raw:
            csv_file.writerow(item)
    return issues_in_query

def collect_all_history(issues):
    history_raw = []
    for history_issue in issues:
        issue = jira.issue(history_issue.key, expand='changelog')
        key = issue.key
        issue_id = issue.id

        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == 'status' or item.field == 'assignee':
                    created_ts = datetime.strptime(str(history.created), '%Y-%m-%dT%H:%M:%S.%f%z')
                    created_ts = datetime.strftime(created_ts, '%Y-%m-%d %H:%M:%S')
                    author_name = history.author.displayName
                    author_name = author_name.replace("Erdélyi 💛 ", "Erdelyi")
                    history_item = [key, issue_id, author_name, created_ts, item.field, item.fromString, item.toString]
                    history_raw.append(history_item)

    history_raw = sorted(history_raw, key=lambda x: (x[1], x[3]))

    with open(ticket_history_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(history_header)
        for item in history_raw:
            csv_file.writerow(item)

def filter_non_printable(str):
    return ''.join([c for c in str if ord(c) > 31 or ord(c) == 9])

jira = JIRA(options, basic_auth=(jira_user,jira_apikey))
all_epics = get_all_epics(jql_string_all_epics)
issues_in_proj = run_JQL_query(jql_string_sprint)
collect_all_history(issues_in_proj)

print("--- Execution time: %s seconds ---" % (time.time() - start_time))
