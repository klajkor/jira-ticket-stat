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


if __name__ == '__main__':
    jira = JIRA(options, basic_auth=(jira_user, jira_apikey))
    print(jira.sprint_info(0, jira_stat_lib.get_sprint_id(jira, jira_stat_lib.dev_sprint_board_id, "CCP Dev Sprint 40")))
    print("#####-----------------#####")
    all_sprints = jira_stat_lib.get_all_sprints(jira, jira_stat_lib.dev_sprint_board_id)
    for sprint in all_sprints:
        print(sprint)
    print("#####-----------------#####")

    # sprint_report(dev_sprint_board_id, get_sprint_id(jira, dev_sprint_board_id, "CCP Dev Sprint 40"))

    jira.close()
    print("--- Execution time: %s seconds ---" % (time.time() - start_time))
