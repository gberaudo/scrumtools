import argparse
import logging
from jira import JIRA
from datetime import datetime

from .util import str2bool, create_summary

log = logging.getLogger("tool")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA epic info tool")
    parser.add_argument("project", type=str, help="the project name.")
    parser.add_argument("--since", type=str, help="a minimum date like 2020.12.07.")
    parser.add_argument("--until", type=str, help="a maximum date like 2020.12.07.")
    parser.add_argument("--urls", type=str2bool, nargs="?", const=True, help="Show urls", default=False)
    parser.add_argument("--debug", type=str2bool, nargs="?", const=True, default=False)

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    project_id = args.project

    start_date = None
    if args.since:
        start_date = datetime.strptime(args.since, '%Y.%m.%d')
    end_date = None
    if args.until:
        end_date = datetime.strptime(args.until, '%Y.%m.%d')

    jql = f'issuetype in (Epic, Story, Bug, Task, subTaskIssueTypes()) AND project = {project_id}'

    jiraobj = JIRA({"server": "https://jira.camptocamp.com"})
    results = jiraobj.search_issues(jql)
    create_summary(jiraobj, results, start_date, end_date, args.urls)


if __name__ == "__main__":
    main()
