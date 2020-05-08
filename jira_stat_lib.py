import sys, os, traceback, argparse
from datetime import datetime
from datetime import timedelta
import time
import re
import ast
import csv
from operator import attrgetter

from jira import JIRA
import pandas as pd
import numpy as np
import logging
import json

global FMT_date_time, ticket_header, dev_sprint_board_id
FMT_date_time = '%Y-%m-%d %H:%M:%S'
FMT_jql_date_time = '%Y-%m-%d %H:%M'
ticket_header = ['Issue key', 'Type', 'Summary', 'Status', 'Release', 'Story Point', 'First Sprint', 'Last Sprint',
                 'Created', 'Updated', 'Epic Key', 'Epic Title', 'Labels', 'URL']
dev_sprint_board_id = 100  ## "Dev Sprint Board"


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


def get_sprint_id(jira_object, board_id, sprint_name):
    sprint_id = -1
    sprints = jira_object.sprints(board_id)
    for sprint in sprints:
        if sprint.name == sprint_name:
            sprint_id = sprint.id
    return sprint_id


def get_all_sprints(jira_object, board_id, sprint_start_at=0, sprint_max_results=10):
    list_all_sprints = []
    temp_all_sprints = jira_object.sprints(board_id, extended=False, startAt=sprint_start_at, maxResults=sprint_max_results)
    for jira_sprint in temp_all_sprints:
        sprint_info = jira_object.sprint_info(board_id, jira_sprint.id)
        name = sprint_info['name']
        sprint_id = sprint_info['id']
        if sprint_info['isoStartDate'] != 'None':
            start_date = datetime.strptime(sprint_info['isoStartDate'], '%Y-%m-%dT%H:%M:%S%z')
        else:
            start_date = datetime.strptime('2211-11-22T22:11:22+0100', '%Y-%m-%dT%H:%M:%S%z')
        if sprint_info['isoEndDate'] != 'None':
            end_date = datetime.strptime(sprint_info['isoEndDate'], '%Y-%m-%dT%H:%M:%S%z')
        else:
            end_date = None
        if sprint_info['isoCompleteDate'] != 'None':
            complete_date = datetime.strptime(sprint_info['isoCompleteDate'], '%Y-%m-%dT%H:%M:%S%z')
        else:
            complete_date = None
        state = sprint_info['state']
        incomplete_estimates = 0
        complete_estimates = 0
        complete_stories = 0
        fixed_bugs = 0

        sprint_jql = 'project = CCP AND type in (Story, Bug) AND statusCategory in (Done) AND Sprint in ("' + name
        sprint_jql += '") AND statusCategoryChangedDate >= "' + datetime.strftime(start_date, FMT_jql_date_time) + '"'
        sprint_jql += ' AND statusCategoryChangedDate <= "' + datetime.strftime(end_date, FMT_jql_date_time) + '"'
        # print(sprint_jql)
        # issues_in_query = []
        issues_in_query = jira_object.search_issues(sprint_jql, maxResults=100)
        for issue in issues_in_query:
            if issue.fields.issuetype.name == 'Story':
                complete_stories += 1
            if issue.fields.issuetype.name == 'Bug':
                fixed_bugs += 1
            story_point = issue.fields.customfield_10105
            if type(story_point) is float:
                story_point = int(story_point)
            else:
                story_point = 0
            complete_estimates += story_point
        dict_sprint = {'sprint_id': sprint_id, 'name': name, 'state': state, 'start_date': start_date,
                       'end_date': end_date, 'complete_date': complete_date, 'complete_estimates': complete_estimates,
                       'incomplete_estimates': incomplete_estimates, 'complete_stories': complete_stories,
                       'fixed_bugs': fixed_bugs}
        list_all_sprints.append(dict_sprint)
    list_all_sprints = sorted(list_all_sprints, key=lambda x: (x['start_date'], x['name']))
    return list_all_sprints

