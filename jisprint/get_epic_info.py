import argparse
import logging
from .util import get_jiraobj, str2bool, create_summary

log = logging.getLogger("tool")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA epic info tool")
    parser.add_argument("epic", type=str, help="the epic id.")
    parser.add_argument("--urls", type=str2bool, nargs="?", const=True, help="Show urls", default=False)
    parser.add_argument("--debug", type=str2bool, nargs="?", const=True, default=False)

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    epic_id = args.epic

    jql = f'issuetype in (Epic, Story, Bug, Task, subTaskIssueTypes()) AND "epic link" = {epic_id}'

    jiraobj = get_jiraobj()
    results = jiraobj.search_issues(jql)
    create_summary(jiraobj, results, None, None, args.urls)


if __name__ == "__main__":
    main()
