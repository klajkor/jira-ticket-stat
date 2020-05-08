# library modules
import time
from jira import JIRA
from operator import attrgetter

# local include files
import jira_credentials
import jira_stat_lib as jsl

start_time = time.time()

jira_user = jira_credentials.login['jira_user']
jira_apikey = jira_credentials.login['jira_apikey']
jira_server = 'https://bmigroup.atlassian.net'
options = {
    'server': jira_server
}


if __name__ == '__main__':
    jira = JIRA(options, basic_auth=(jira_user, jira_apikey))
    # print(jira.sprint_info(0, jsl.get_sprint_id(jira, jsl.dev_sprint_board_id, "CCP Dev Sprint 40")))
    all_sprints = jsl.get_all_sprints(jira, jsl.dev_sprint_board_id, 90, 100)
    for sprint in all_sprints:
        print(sprint)
    print("#####-----------------#####")

    # sprint_report(dev_sprint_board_id, get_sprint_id(jira, dev_sprint_board_id, "CCP Dev Sprint 40"))

    jira.close()
    print("--- Execution time: %s seconds ---" % (time.time() - start_time))
