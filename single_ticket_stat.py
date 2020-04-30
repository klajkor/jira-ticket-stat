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

# local include files
import jira_credentials
import jira_stat_lib

start_time = time.time()

jira_user = jira_credentials.login['jira_user']
jira_apikey = jira_credentials.login['jira_apikey']
jira_server = 'https://bmigroup.atlassian.net'
options = {
    'server': jira_server
}
jql_string_tahir = 'issueKey in (CCP-764,CCP-1431,CCP-1543,CCP-1584,CCP-1585,CCP-1605,CCP-1607,CCP-1608,CCP-1609,' \
                   'CCP-1610,CCP-1619,CCP-1620,CCP-1633,CCP-1634,CCP-1635,CCP-1642,CCP-1643,CCP-1644,CCP-1648,' \
                   'CCP-1649,CCP-1653,CCP-1654,CCP-1655,CCP-1656,CCP-1660,CCP-1665,CCP-1669,CCP-1670,CCP-1672,' \
                   'CCP-1683) '

ticket_list_file = 'ticket_list.csv'
ticket_history_file = 'ticket_history.csv'
ticket_transition_file = 'ticket_transition.csv'
history_header = ['Issue key', 'Issue ID', 'Author', 'Timestamp', 'Item type', 'From', 'To']
transition_header = ['Issue key', 'Issue ID', 'Previous Status', 'New Status', 'Prev TS', 'New TS', 'Elapsed time',
                     'Author']
all_epics = {}
issues_in_proj = {}

ticket_phases_map = {'In Progress': 'Dev Time', 'ToDo': 'Backlog'}


def collect_all_history(issues):
    history_raw = []
    transition_raw = []
    for history_issue in issues:
        issue = jira.issue(history_issue.key, expand='changelog')
        key = issue.key
        issue_id = issue.id
        prev_ts = datetime.strptime(str(issue.fields.created), '%Y-%m-%dT%H:%M:%S.%f%z')
        prev_ts = datetime.strftime(prev_ts, jira_stat_lib.FMT_date_time)
        changelog_histories = issue.changelog.histories
        # print(type(changelog_histories))
        changelog_histories = sorted(changelog_histories, key=lambda x: x.created)
        for history in changelog_histories:
            for item in history.items:
                if item.field == 'status' or item.field == 'assignee':
                    created_ts = datetime.strptime(str(history.created), '%Y-%m-%dT%H:%M:%S.%f%z')
                    created_ts = datetime.strftime(created_ts, jira_stat_lib.FMT_date_time)
                    author_name = history.author.displayName
                    author_name = author_name.replace("Erdélyi 💛 ", "Erdelyi")
                    history_item = [key, issue_id, author_name, created_ts, item.field, item.fromString, item.toString]
                    history_raw.append(history_item)
                    if item.field == 'status':
                        # elapsed = datetime.strftime(tdelta, FMT_date_time)
                        tdelta = ''
                        transition_item = [key, issue_id, item.fromString, item.toString, prev_ts, created_ts, tdelta,
                                           author_name]
                        transition_raw.append(transition_item)
                        prev_ts = created_ts

    # history_raw = sorted(history_raw, key=lambda x: (x[1], x[3]))
    # transition_raw = sorted(transition_raw, key=lambda x: (x[1], x[4]))
    for item in transition_raw:
        tdelta = datetime.strptime(item[5], jira_stat_lib.FMT_date_time) - datetime.strptime(item[4],
                                                                                             jira_stat_lib.FMT_date_time)
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


def sprint_report(board_id, sprint_id):
    # Calculate Incompleted Issues
    sum_incompl = jira.incompletedIssuesEstimateSum(board_id, sprint_id)
    # Completed
    sum_compl = jira.completedIssuesEstimateSum(board_id, sprint_id)

    # Print all
    print
    "Sum Incompleted Issues: ", sum_incompl
    print
    "Sum Completed Issues ", sum_compl



if __name__ == '__main__':
    jira = JIRA(options, basic_auth=(jira_user, jira_apikey))
    # collect_all_history(issues_in_proj)
    # print("#####-----------------#####")
    # print(jira.sprint_info(0, get_sprint_id(jira, "CCP Dev Sprint 40", dev_sprint_board_id)))
    print("#####-----------------#####")
    all_sprints = get_all_sprints()
    print(all_sprints)
    print("#####-----------------#####")
    print(all_sprints[-1]['start_date'])

    # sprint_report(dev_sprint_board_id, get_sprint_id(jira, "CCP Dev Sprint 40", dev_sprint_board_id))

    jira.close()
    print("--- Execution time: %s seconds ---" % (time.time() - start_time))
