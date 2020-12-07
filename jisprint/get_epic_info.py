import argparse
import logging
import os.path

import dateutil.parser
from jira import JIRA

from .util import str2bool, create_summary

log = logging.getLogger("tool")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA epic info tool")
    parser.add_argument("epic", type=str, help="the epic id. ")
    parser.add_argument("--urls", type=str2bool, nargs="?", const=True, help="Show urls", default=False)
    parser.add_argument("--host", type=str, default="jira.camptocamp.com", help="the JIRA server host")
    parser.add_argument(
        "--debug", type=str2bool, nargs="?", const=True, help="be more verbose", default=False
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    jiraobj = JIRA({"server": "https://" + args.host})

    epic_id = args.epic

    jql = f'"epic link" = {epic_id} AND issuetype in (Story, Bug, Task, subTaskIssueTypes())'

    results = jiraobj.search_issues(jql)

    start_date = None
    end_date = None
    create_summary(jiraobj, results, start_date, end_date, args.urls)


if __name__ == "__main__":
    main()
