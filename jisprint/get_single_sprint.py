import argparse
import logging
import os.path
import os

import datetime
import dateutil.parser
from jira import JIRA

from .util import read_project_from_scrum_file, str2bool, guess_sprint_id_or_fail, create_summary, read_board_from_scrum_file

log = logging.getLogger("tool")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA spring summary tool")
    parser.add_argument('--backlog', type=str2bool, nargs="?", const=True, help="Open backlog", default=False)
    parser.add_argument("--sprint", type=int, default=0, help="the sprint id. ")
    parser.add_argument("--project", type=str, help="the project name.")
    parser.add_argument("--urls", type=str2bool, nargs="?", const=True, help="Show urls", default=False)
    parser.add_argument("--subtasks", type=str2bool, nargs="?", const=True, help="Do not merge subtasks in their parent", default=False)
    parser.add_argument("--workedon", type=str2bool, nargs="?", const=True, help="Show who worked on what", default=False)
    parser.add_argument("--host", type=str, default="jira.camptocamp.com", help="the JIRA server host")
    parser.add_argument(
        "--allworklogs", type=str2bool, nargs="?", const=True, help="Include all worklogs", default=False
    )
    parser.add_argument(
        "--overdue", type=str2bool, nargs="?", const=True, help="Include worklogs since start of sprint", default=False
    )
    parser.add_argument(
        "--recent", type=str2bool, nargs="?", const=True, help="Include only recent worklogs", default=False
    )
    parser.add_argument(
        "--debug", type=str2bool, nargs="?", const=True, help="be more verbose", default=False
    )
    parser.add_argument(
        "--retro", type=str2bool, nargs="?", const=True, help="Generate a retrospective template", default=False
    )

    args = parser.parse_args()

    if args.backlog:
        board = read_board_from_scrum_file()
        os.system(f'browse "https://jira.camptocamp.com/secure/RapidBoard.jspa?rapidView={board}&view=planning.nodetail&issueLimit=100"')
        return

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    jiraobj = JIRA({"server": "https://" + args.host})

    sprint_id = args.sprint
    if sprint_id == 0:
        sprint_id = guess_sprint_id_or_fail(jiraobj)

    project = args.project
    if project is None:
        project = read_project_from_scrum_file()

    jql = f"Sprint = {sprint_id} AND project = {project} AND issuetype in (Story, Bug, Task, subTaskIssueTypes())"

    results = []
    prc = 0
    # FIXME: poor man all results iteration, I would expect the lib to do that for me...
    while True:
        partial_results = jiraobj.search_issues(jql, startAt=prc, maxResults=50)
        results.extend(partial_results)
        prc += len(partial_results)
        if prc == partial_results.total:
            break

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
    if args.recent:
        td = datetime.timedelta(15)
        now = datetime.datetime.now()
        start_date = now - td
    if args.allworklogs:
        start_date = None
        end_date = None
    if args.overdue:
        end_date = None
    create_summary(jiraobj, results, start_date, end_date, args.urls, not args.subtasks, args.workedon)

    if args.retro:
        template = """
Security

Production

Announces

Feedback
    client:
    Product Owner:
    devs:
    Scrum Master:

Technical corner

Improving actions review

Improving actions

当番 (toban: person on duty)
Daily:
Review:
Planning:"""
        print(template)


if __name__ == "__main__":
    main()
