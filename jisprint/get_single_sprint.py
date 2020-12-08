import argparse
import logging
import os.path

import dateutil.parser
from jira import JIRA

from .util import str2bool, guess_sprint_id_or_fail, create_summary

log = logging.getLogger("tool")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA spring summary tool")
    parser.add_argument("--sprint", type=int, default=0, help="the sprint id. ")
    parser.add_argument("--urls", type=str2bool, nargs="?", const=True, help="Show urls", default=False)
    parser.add_argument("--host", type=str, default="jira.camptocamp.com", help="the JIRA server host")
    parser.add_argument(
        "--allworklogs", type=str2bool, nargs="?", const=True, help="Include all worklogs", default=False
    )
    parser.add_argument(
        "--debug", type=str2bool, nargs="?", const=True, help="be more verbose", default=False
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    jiraobj = JIRA({"server": "https://" + args.host})

    sprint_id = args.sprint
    if sprint_id == 0:
        sprint_id = guess_sprint_id_or_fail(jiraobj)

    jql = "Sprint = {sprint_id} AND issuetype in (Story, Bug, Task, subTaskIssueTypes())".format(
        sprint_id=sprint_id
    )

    results = jiraobj.search_issues(jql)
    sprint = jiraobj.sprint(sprint_id)
    start_date = dateutil.parser.parse(sprint.startDate)
    end_date = dateutil.parser.parse(sprint.endDate)
    delta = (end_date - start_date).days
    goal = sprint.goal if "goal" in sprint.raw else ""
    print("Sprint infos: %s %s %s" % (sprint_id, sprint.name, goal))
    print("{delta}d {start_date} -> {end_date}".format(delta=delta, start_date=start_date, end_date=end_date))

    # The start date is forced to be at 00:00:00, the sprints starts the day of the planning, at 00:00:00.
    # The end date is forced to be at 00:00:00, the sprint ends the day before at 23:59:59).
    # Reasonning:
    # When doing the retro we do not have the worklogs of the day so the time of the
    # demo/retro/planning is to be counted in the new sprint.
    # This is compatible with some worklogs starting at 00:00:00: they will be included in the
    # current sprint.
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = end_date.replace(hour=0, minute=0, second=0)
    if args.allworklogs:
        start_date = None
        end_date = None
    create_summary(jiraobj, results, start_date, end_date, args.urls)


if __name__ == "__main__":
    main()
