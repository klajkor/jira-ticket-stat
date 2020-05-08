# library modules
import time
from jira import JIRA

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
jql_string_R5 = 'project = CCP AND fixVersion in ("Release 5.0") ORDER BY type DESC,  key ASC'
jql_string_R51 = 'project = CCP AND fixVersion in ("Release 5.1") ORDER BY type DESC,  key ASC'
jql_string_R6 = 'project = CCP AND fixVersion in ("Release 6.0") ORDER BY type DESC,  key ASC'
jql_string_all_epics = 'project = CCP AND type in (Epic) ORDER BY KEY ASC'
jql_string_sprint = 'issueKey in (CCP-640,CCP-1431,CCP-1543,CCP-1571,CCP-1633,CCP-1643,CCP-1644,CCP-1677)'
jql_string_lms = 'project = CCP AND type in (Story) AND "Epic Link" in (CCP-1666, CCP-1651, CCP-1652) ORDER BY key ASC'
jql_string_lms_p1 = 'project = CCP AND type in (Story) AND "Epic Link" = CCP-1666 ORDER BY key ASC'
jql_string_sprint = 'issueKey in (CCP-640,CCP-1633,CCP-1643,CCP-1644,CCP-1649,CCP-1656,CCP-1669,CCP-1721, CCP-1431,CCP-1543,CCP-1571,CCP-1610,CCP-1665,CCP-1672,CCP-1677) '

ticket_list_file = 'ticket_list.csv'
all_epics = {}
issues_in_proj = {}

if __name__ == '__main__':
    jira = JIRA(options, basic_auth=(jira_user, jira_apikey))
    all_epics = jira_stat_lib.get_all_epics(jira, jql_string_all_epics)
    issues_in_proj = jira_stat_lib.export_issues_to_csv(jira, jql_string_sprint, all_epics, ticket_list_file)
    print("#####----------------------------------#####")
    print("Tickets exported to: ", ticket_list_file)
    print("#####----------------------------------#####")
    jira.close()
    print("--- Execution time: %s seconds ---" % (time.time() - start_time))