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
jql_string_R51 = 'project = CCP AND fixVersion in ("Release 5.1") ORDER BY type DESC,  key ASC'
jql_string_R6 = 'project = CCP AND fixVersion in ("Release 6.0") ORDER BY type DESC,  key ASC'
jql_string_all_epics = 'project = CCP AND type in (Epic) ORDER BY KEY ASC'
jql_string_sprint = 'issueKey in (CCP-443,CCP-628,CCP-640,CCP-1431,CCP-1543,CCP-1571,CCP-1580,CCP-1582,CCP-1617,CCP-1625)'
jql_string_lms = 'project = CCP AND type in (Story) AND "Epic Link" in (CCP-1666, CCP-1651, CCP-1652) ORDER BY key ASC'
jql_string_lms_p1 = 'project = CCP AND type in (Story) AND "Epic Link" = CCP-1666 ORDER BY key ASC'
jql_string_tahir = 'issueKey in (CCP-1582,CCP-628,CCP-640,CCP-1508,CCP-1580,CCP-443,CCP-1294,CCP-1295,CCP-1535,CCP-1595,CCP-1602,CCP-1603,CCP-1617,CCP-1640)'

FMT_date_time = '%Y-%m-%d %H:%M:%S'
ticket_list_file = 'ticket_list.csv'
ticket_history_file = 'ticket_history.csv'
ticket_transition_file = 'ticket_transition.csv'
ticket_header = ['Issue key', 'Type', 'Summary', 'Status', 'Release', 'Story Point', 'First Sprint', 'Last Sprint', 'Created', 'Updated', 'Epic Key', 'Epic Title', 'Labels', 'URL']
ticket_raw = []
history_header = ['Issue key', 'Issue ID', 'Author', 'Timestamp', 'Item type', 'From', 'To']
transition_header = ['Issue key', 'Issue ID', 'Previous Status', 'New Status', 'Prev TS', 'New TS', 'Elapsed time', 'Author']
all_epics = {}
issues_in_proj = {}

ticket_phases_map = {'In Progress': 'Dev Time', 'ToDo': 'Backlog'}

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
        issue_created_ts = datetime.strftime(issue_created_ts, FMT_date_time)
        issue_updated_ts = datetime.strptime(str(issue.fields.updated), '%Y-%m-%dT%H:%M:%S.%f%z')
        issue_updated_ts = datetime.strftime(issue_updated_ts, FMT_date_time)
        epic_link = issue.fields.customfield_10006
        epic_link_title = ""
        if type(epic_link) is str:
            epic_link_title = all_epics.get(epic_link)
        all_labels = []
        labels = issue.fields.labels
        for i in labels:
            all_labels.append(i)
        url = issue.permalink()
        ticket_item = [issue.key, type_name, summary, status, version_name, story_point, first_sprint, last_sprint, issue_created_ts, issue_updated_ts, epic_link, epic_link_title, all_labels, url]
        ticket_raw.append(ticket_item)
    with open(ticket_list_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(ticket_header)
        for item in ticket_raw:
            csv_file.writerow(item)
    return issues_in_query

def collect_all_history(issues):
    history_raw = []
    transition_raw = []
    for history_issue in issues:
        issue = jira.issue(history_issue.key, expand='changelog')
        key = issue.key
        issue_id = issue.id
        prev_ts = datetime.strptime(str(issue.fields.created), '%Y-%m-%dT%H:%M:%S.%f%z')
        prev_ts = datetime.strftime(prev_ts, FMT_date_time)
        changelog_histories = issue.changelog.histories
        #print(type(changelog_histories))
        changelog_histories = sorted(changelog_histories, key=lambda x: x.created)
        for history in changelog_histories:
            for item in history.items:
                if item.field == 'status' or item.field == 'assignee':
                    created_ts = datetime.strptime(str(history.created), '%Y-%m-%dT%H:%M:%S.%f%z')
                    created_ts = datetime.strftime(created_ts, FMT_date_time)
                    author_name = history.author.displayName
                    author_name = author_name.replace("Erdélyi 💛 ", "Erdelyi")
                    history_item = [key, issue_id, author_name, created_ts, item.field, item.fromString, item.toString]
                    history_raw.append(history_item)
                    if item.field == 'status':
                        #elapsed = datetime.strftime(tdelta, FMT_date_time)
                        tdelta = ''
                        transition_item = [key, issue_id, item.fromString, item.toString, prev_ts, created_ts, tdelta, author_name]
                        transition_raw.append(transition_item)
                        prev_ts = created_ts

    #history_raw = sorted(history_raw, key=lambda x: (x[1], x[3]))
    #transition_raw = sorted(transition_raw, key=lambda x: (x[1], x[4]))
    for item in transition_raw:
        tdelta = datetime.strptime(item[5], FMT_date_time) - datetime.strptime(item[4], FMT_date_time)
        item[6] = tdelta

    with open(ticket_history_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(history_header)
        for item in history_raw:
            csv_file.writerow(item)

    with open(ticket_transition_file, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(transition_header)
        for item in transition_raw:
            csv_file.writerow(item)

def filter_non_printable(str):
    return ''.join([c for c in str if ord(c) > 31 or ord(c) == 9])

jira = JIRA(options, basic_auth=(jira_user,jira_apikey))
all_epics = get_all_epics(jql_string_all_epics)
issues_in_proj = run_JQL_query(jql_string_R51)
#collect_all_history(issues_in_proj)

print("--- Execution time: %s seconds ---" % (time.time() - start_time))
