import argparse
import logging
import sys
from pprint import pprint

import dateutil.parser
from jira import JIRA

log = logging.getLogger('tool')

# See https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

userCache = {}
def get_user(key):
    if key in userCache:
        return userCache[key]
    if 'JIRAUSER' in key:
        # find real name associated to that cryptic key
        username = jira.find('user?key=%s' % key).name
        userCache[key] = username
        return username
    else:
        return key


def get_time_spent_by_user(issues):
    by_user = {}
    all_seconds = 0
    for issue in issues:
        worklogs = jira.worklogs(issue.id)
        log.debug('Getting worklog of issue %s: %s', issue.key, issue.fields.summary)
        count = 0
        for w in worklogs:
            user = get_user(w.author.key)
            spent = w.timeSpentSeconds
            all_seconds = all_seconds + spent
            count = count + spent
            by_user[user] = by_user.get(user, 0) + spent
            log.debug('-> %s %s on %s: %s', user, w.timeSpent, w.updated, w.comment or '')
        log.debug('Time spent check: %s ==? %s', count, issue.fields.timespent)
    return by_user, all_seconds


def get_fast_time_spent(issues):
    all_seconds = 0
    for issue in issues:
        all_seconds = all_seconds + (issue.fields.timespent or 0)  # is it OK to skip like this?
    return all_seconds


def round1(value):
    return round(10 * value) / 10


def round_object(obj, divisor=1):
    return {key: round1(value / divisor) for key, value in obj.items()}


def to_working_days(seconds):
    return seconds / (8.4 * 3600)


def create_summary(issues):
    done_sp = 0
    failed_sp = 0
    formatted_list = []
    all_timespent = 0
    for issue in issues:
        fields = issue.fields
        issuetype = fields.issuetype.name
        category_key = fields.status.statusCategory.key
        summary = fields.summary
        key = issue.key
        if issuetype == 'Sub-task':
          key = fields.parent.key + '/' + key
        storypoints = getattr(fields, 'customfield_10006', None) or 0
        # remaining = fields.timeestimate
        time_spent = fields.timespent or 0
        all_timespent = all_timespent + time_spent
        days_spent = round1(to_working_days(time_spent))
        formatted = "{category_key} {issuetype} {days_spent} / {storypoints}sp: {key} {summary}".format(
            category_key=category_key,
            issuetype=issuetype,
            key=key,
            summary=summary,
            storypoints=int(storypoints),
            days_spent=days_spent,
        )
        formatted_list.append(formatted)
        if category_key == "done":
            done_sp = done_sp + storypoints
        else:
            failed_sp = failed_sp + storypoints
    formatted_list = sorted(formatted_list)
    print("\n".join(formatted_list))
    print("storypoints done: %d" % done_sp)
    print("storypoints failed: %d" % failed_sp)
    days_spent = to_working_days(all_timespent)
    print("days spent: %s" % round1(days_spent))
    print("velocity: %s" % str(round1(done_sp / days_spent)))

    total = 0
    if args.users:
        by_user, total = get_time_spent_by_user(issues)
        print(round_object(by_user, 1 / to_working_days(1)))
    else:
        total = get_fast_time_spent(issues)
    if total != all_timespent:
        log.error("time spen mismatch: %s == %s" % (total, all_timespent))


def get_sprint_infos(sprint_id):
    sprint = jira.sprint(sprint_id)
    start_date = dateutil.parser.parse(sprint.startDate)
    end_date = dateutil.parser.parse(sprint.endDate)
    delta = (end_date - start_date).days
    print("Sprint infos: %s %s" % (sprint.name, sprint.goal))
    print("{delta}d {start_date} -> {end_date}".format(delta=delta, start_date=start_date, end_date=end_date))


def main()
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA spring summary tool")
    parser.add_argument("host", type=str, help="the JIRA server host")
    parser.add_argument("sprint", type=int, help="the sprint id")
    parser.add_argument("--verbose", type=str2bool, nargs='?', const=True, help="be verbose", default=False)
    parser.add_argument("--users", type=str2bool, nargs='?', const=True, help="show user info", default=False)

    args = parser.parse_args()


    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug('Debug mode enabled')

    jira = JIRA({"server": "https://" + args.host})

    jql = "Sprint = {sprint_id} AND issuetype in (Story, Bug, Task, subTaskIssueTypes())".format(
        sprint_id=args.sprint
    )

    results = jira.search_issues(jql)
    print("Found %d results" % len(results))

    get_sprint_infos(args.sprint)
    create_summary(results)

if __name__ == "__main__":
    main()
