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
def get_user(jiraobj, key):
    if key in userCache:
        return userCache[key]
    if 'JIRAUSER' in key:
        # find real name associated to that cryptic key
        username = jiraobj.find('user?key=%s' % key).name
        userCache[key] = username
        return username
    else:
        return key


def get_time_spent_by_user(jiraobj, issue, since, until, by_user):
    all_seconds = 0
    worklogs = jiraobj.worklogs(issue.id)
    log.debug('Getting worklog of issue %s: %s', issue.key, issue.fields.summary)
    count = 0
    skipped = 0
    for w in worklogs:
        spent = w.timeSpentSeconds
        user = get_user(jiraobj, w.author.key)
        started = dateutil.parser.parse(w.started)
        started = started.replace(tzinfo=None)  # trash timezone to be consistent
        if (started > until or started < since):
            skipped = skipped + spent
            log.debug('----> skipped: %s %s on %s: %s', user, w.timeSpent, started, w.comment or '')
            continue
        all_seconds = all_seconds + spent
        count = count + spent
        by_user[user] = by_user.get(user, 0) + spent
        log.debug('-> %s %s on %s: %s', user, w.timeSpent, started, w.comment or '')
    return all_seconds, skipped


def round1(value):
    return round(10 * value) / 10


def round_object(obj, divisor=1):
    return {key: round1(value / divisor) for key, value in obj.items()}


def to_working_days(seconds):
    return seconds / (8.4 * 3600)


def create_summary(jiraobj, issues, start_date, end_date):
    done_sp = 0
    failed_sp = 0
    formatted_list = []
    all_timespent = 0
    all_skipped_timespent = 0
    time_spent_by_user = {}
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
        # not using fields.timespent since it may include worklogs outside the sprint time span
        time_spent, skipped_time_spent =  get_time_spent_by_user(jiraobj, issue, start_date, end_date, time_spent_by_user)
        all_timespent = all_timespent + time_spent
        all_skipped_timespent = all_skipped_timespent + skipped_time_spent
        days_spent = round1(to_working_days(time_spent))
        formatted = "{category_key:5.5} {issuetype:5.5} {days_spent}d / {storypoints}sp {key} {summary}".format(
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
    print(round_object(time_spent_by_user, 1 / to_working_days(1)))
    if skipped_time_spent != 0:
        log.warning("Some worklogs were skipped because outside the sprint time span: %s days" % round1(to_working_days(all_skipped_timespent)))


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA spring summary tool")
    parser.add_argument("host", type=str, help="the JIRA server host")
    parser.add_argument("sprint", type=int, help="the sprint id")
    parser.add_argument("--debug", type=str2bool, nargs='?', const=True, help="be more verbose", default=False)

    args = parser.parse_args()


    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
        log.debug('Debug mode enabled')

    jiraobj = JIRA({"server": "https://" + args.host})

    jql = "Sprint = {sprint_id} AND issuetype in (Story, Bug, Task, subTaskIssueTypes())".format(
        sprint_id=args.sprint
    )

    results = jiraobj.search_issues(jql)
    sprint = jiraobj.sprint(args.sprint)
    start_date = dateutil.parser.parse(sprint.startDate)
    end_date = dateutil.parser.parse(sprint.endDate)
    # Some worklogs are created at 0:0:0, so to consider them during the sprint
    # we extend the time span of the sprint to the entire start and end days
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = end_date.replace(hour=23, minute=0, second=0)
    delta = (end_date - start_date).days
    print("Sprint infos: %s %s" % (sprint.name, sprint.goal))
    print("{delta}d {start_date} -> {end_date}".format(delta=delta, start_date=start_date, end_date=end_date))

    create_summary(jiraobj, results, start_date, end_date)

if __name__ == "__main__":
    main()
