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

global FMT_date_time, ticket_header
FMT_date_time = '%Y-%m-%d %H:%M:%S'
ticket_header = ['Issue key', 'Type', 'Summary', 'Status', 'Release', 'Story Point', 'First Sprint', 'Last Sprint',
                 'Created', 'Updated', 'Epic Key', 'Epic Title', 'Labels', 'URL']


def get_all_epics(jira_object, query_string):
    tmp_dict = {}
    issues_in_proj = jira_object.search_issues(query_string, maxResults=200)
    for issue in issues_in_proj:
        tmp_dict[issue.key] = issue.fields.summary
    return tmp_dict


def export_issues_to_csv(jira_object, query_string, all_epics_dict, csv_file_name):
    ticket_raw = []
    issues_in_query = jira_object.search_issues(query_string, maxResults=1000)
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
            epic_link_title = all_epics_dict.get(epic_link)
        all_labels = []
        labels = issue.fields.labels
        for i in labels:
            all_labels.append(i)
        url = issue.permalink()
        ticket_item = [issue.key, type_name, summary, status, version_name, story_point, first_sprint, last_sprint,
                       issue_created_ts, issue_updated_ts, epic_link, epic_link_title, all_labels, url]
        ticket_raw.append(ticket_item)
    with open(csv_file_name, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(ticket_header)
        for item in ticket_raw:
            csv_file.writerow(item)
    return issues_in_query


def filter_non_printable(string_par):
    return ''.join([c for c in string_par if ord(c) > 31 or ord(c) == 9])
