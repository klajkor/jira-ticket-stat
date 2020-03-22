# library modules
import sys, os, traceback, argparse
from datetime import datetime
import time
import re
import ast

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

ticket = 'CCP-1545'
issue = jira.issue(ticket, expand='changelog')
summary = issue.fields.summary
print('ticket: ', ticket, issue.fields.summary)

print(f"Changes from issue: {issue.key} {issue.fields.summary}")
print(f"Number of Changelog entries found: {issue.changelog.total}") # number of changelog entries (careful, each entry can have multiple field changes)

for history in issue.changelog.histories:
    print(f"Author: {history.author}") # person who did the change
    print(f"Timestamp: {history.created}") # when did the change happen?
    #print("\nListing all items that changed:")

    for item in history.items:
        if item.field == 'status':
            print(f"Field name: {item.field}") # field to which the change happened
            print(f"Changed from: {item.fromString}") # old value, item.from might be better in some cases depending on your needs.
            print(f"Changed to: {item.toString}") # new value, item.to might be better in some cases depending on your needs.
            print()