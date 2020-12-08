import argparse
import logging
import os.path

import dateutil.parser
from jira import JIRA

log = logging.getLogger("tool")

# See https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def guess_sprint_id_or_fail(jiraobj):
    log.debug("Trying to guess the sprint id")
    if not os.path.exists(".scrum"):
        raise Exception("Could not guess the sprint id. No .scrum file found.")
    with open(".scrum", "r") as f:
        for line in f:
            name, var = line.partition("=")[::2]
            if name.strip() == "board":
                board_id = var.strip()
                sprints = jiraobj.sprints(board_id)
                for s in sprints:
                    if s.state not in ("CLOSED", "FUTURE"):
                        print("%s %s (%s)" % (s.name, s.id, s.state))
                actives = [s for s in sprints if s.state == "ACTIVE"]
                if len(actives) == 0:
                    raise Exception("No active sprint in board %s" % board_id)
                if len(actives) > 1:
                    raise Exception(
                        "Several sprints are active in board %s: %s" % (board_id, [s.id for s in actives])
                    )
                return actives[0].id
        raise Exception("No board id found in the .scrum file")


userCache = {}


def get_user(jiraobj, key):
    if key in userCache:
        return userCache[key]
    if "JIRAUSER" in key:
        # find real name associated to that cryptic key
        username = jiraobj.find("user?key=%s" % key).name
        userCache[key] = username
        return username
    return key


def get_time_spent_by_user(jiraobj, issue, since, until, by_user):
    all_seconds = 0
    worklogs = jiraobj.worklogs(issue.id)
    log.debug("Getting worklog of issue %s: %s", issue.key, issue.fields.summary)
    count = 0
    skipped = 0
    for w in worklogs:
        spent = w.timeSpentSeconds
        user = get_user(jiraobj, w.author.key)
        started = dateutil.parser.parse(w.started)
        started = started.replace(tzinfo=None)  # trash timezone to be consistent
        if since is not None and until is not None and (started < since or started >= until):
            log.debug("----> skipped: %s %s on %s: %s", user, w.timeSpent, started, w.comment or "")
            skipped += spent
            continue
        all_seconds += spent
        count += spent
        by_user[user] = by_user.get(user, 0) + spent
        log.debug("-> %s %s on %s: %s", user, w.timeSpent, started, w.comment or "")
    return all_seconds, skipped


def round1(value):
    return round(10 * value) / 10


def round2(value):
    return round(100 * value) / 100


def round_object(obj, divisor=1):
    return {key: round1(value / divisor) for key, value in obj.items()}


def to_working_days(seconds):
    return seconds / (8.4 * 3600)


def create_summary(jiraobj, issues, start_date, end_date, show_url):
    done_sp = 0
    failed_sp = 0
    formatted_list = []
    all_timespent = 0
    all_skipped_timespent = 0
    all_bugs_timespent = 0
    all_other_timespent = 0
    time_spent_by_user = {}
    for issue in issues:
        fields = issue.fields
        issuetype = fields.issuetype.name
        category_key = fields.status.statusCategory.key
        summary = fields.summary
        key = issue.key
        # if issuetype == "Sub-task":
        #     key = fields.parent.key + "/" + key
        if show_url:
            summary = "%s/browse/%s " % (jiraobj.client_info(), key) + summary
        storypoints = getattr(fields, "customfield_10006", None) or 0
        # remaining = fields.timeestimate
        # not using fields.timespent since it may include worklogs outside the sprint time span
        time_spent, skipped_time_spent = get_time_spent_by_user(
            jiraobj, issue, start_date, end_date, time_spent_by_user
        )
        all_timespent += time_spent
        all_skipped_timespent += skipped_time_spent
        days_spent = round1(to_working_days(time_spent))
        if issuetype == "Bug":
            all_bugs_timespent += time_spent
        else:
            all_other_timespent += time_spent
        formatted = "{category_key:5.5} {issuetype:5.5} {days_spent}d /{storypoints:>2}sp {key:<11} {status:<16} {summary}".format(
            category_key=category_key,
            issuetype=issuetype,
            key="" if show_url else key + " ",
            summary=summary,
            storypoints=int(storypoints),
            days_spent=days_spent,
            status=str(fields.status),
        )
        formatted_list.append(formatted)
        if category_key == "indeterminate":
            category_key = str(fields.status)
        if category_key in ("done", "Internal review"):
            done_sp += storypoints
        else:
            failed_sp += storypoints
    formatted_list = sorted(formatted_list)
    print("\n".join(formatted_list))
    print("sprint start: %s (including)" % start_date)
    print("sprint end: %s (excluding)" % end_date)
    print("storypoints done: %d" % done_sp)
    print("storypoints failed: %d" % failed_sp)
    days_spent = to_working_days(all_timespent)
    print("days spent: %s" % round1(days_spent))
    days_spent_on_bugs = to_working_days(all_bugs_timespent)
    print("days spent on bugs: %s" % round1(days_spent_on_bugs))
    bugs_ratio = 0 if all_timespent == 0 else round(100 * all_bugs_timespent / all_timespent)
    print("bugs ratio: %s%%" % str(bugs_ratio))
    the_velocity = 0 if days_spent == 0 else round1(done_sp / days_spent)
    print("velocity: %s" % str(the_velocity))
    print("By user:")
    for name, time in round_object(time_spent_by_user, 1 / to_working_days(1)).items():
        print("  {}: {}".format(name, time))
    log.debug(
        "Some worklogs were skipped because outside the sprint time span: %s days",
        round1(to_working_days(all_skipped_timespent)),
    )
