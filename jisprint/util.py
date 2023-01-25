import argparse
import logging
import os.path
from pathlib import Path

import dateutil.parser
from jira import JIRA
from typing import Optional

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


def find_scrum_file() -> Optional[Path]:
    dir = Path.cwd()
    while (dir.root != dir):
        scrum_path = dir.with_name('.scrum')
        if scrum_path.exists():
            return scrum_path
        dir = dir.parent
    print("No .scrum file found.")


def read_board_from_scrum_file():
    scrum_file = find_scrum_file()
    if not scrum_file:
        raise Exception("Could not guess the sprint id.")
    with scrum_file.open("r") as f:
        for line in f:
            name, var = line.partition("=")[::2]
            if name.strip() == "board":
                return var.strip()
    raise Exception("No board id found in the .scrum file")


def guess_sprint_id_or_fail(jiraobj):
    log.debug("Trying to guess the sprint id")
    board_id = read_board_from_scrum_file()
    actives = jiraobj.sprints(board_id, state="active")
    if len(actives) == 0:
        raise Exception("No active sprint in board %s" % board_id)
    if len(actives) > 1:
        raise Exception("Several sprints are active in board %s: %s" % (board_id, [s.id for s in actives]))
    return actives[0].id


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
    skipped = 0
    kept_worklogs = []
    by_user_for_issue = {}
    for w in worklogs:
        spent = w.timeSpentSeconds
        user = get_user(jiraobj, w.author.key)
        started = dateutil.parser.parse(w.started)
        started = started.replace(tzinfo=None)  # trash timezone to be consistent
        if (
            since is not None
            and until is not None
            and (started.timestamp() < since.timestamp() or started.timestamp() >= until.timestamp())
        ):
            log.debug("----> skipped: %s %s on %s: %s", user, w.timeSpent, started, w.comment or "")
            skipped += spent
            continue
        all_seconds += spent
        kept_worklogs.append({"user": user, "spent": spent, "raw": w})
        by_user[user] = by_user.get(user, 0) + spent
        by_user_for_issue[user] = by_user_for_issue.get(user, 0) + spent
        log.debug("-> %s %s on %s: %s", user, w.timeSpent, started, w.comment or "")
    return all_seconds, skipped, kept_worklogs, by_user_for_issue


def round1(value):
    return round(10 * value) / 10


def round2(value):
    return round(100 * value) / 100


def round_object(obj, divisor=1):
    return {key: round1(value / divisor) for key, value in obj.items()}


def to_working_days(seconds):
    return seconds / (8.4 * 3600)


def merge_subtasks(items):
    merged = []
    index = {item["key"]: item for item in items}
    for item in items:
        if item["issuetype"] == "Sub-task":
            parent = index[item["parent"].key]
            parent["days_spent"] += item["days_spent"]
            parent["work_items"] += item["work_items"]
        else:
            merged.append(item)
    return merged


def format_spent_by_user(by_user, minimum=0.15):
    worked = [
        "%s: %sd" % (user, round1(to_working_days(spent)))
        for user, spent in by_user.items()
        if round1(to_working_days(spent)) > minimum
    ]
    joiner = "\n   "
    if len(worked) > 0:
        return joiner + joiner.join(worked)
    else:
        return ""


def create_summary(jiraobj, issues, start_date, end_date, show_url, merged_subtasks=False, worked_on=False):
    done_sp = 0
    failed_sp = 0
    formatted_list = []
    all_timespent = 0
    all_skipped_timespent = 0
    all_bugs_timespent = 0
    all_other_timespent = 0
    time_spent_by_user = {}
    items = []

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
        time_spent, skipped_time_spent, work_items, by_user_for_issue = get_time_spent_by_user(
            jiraobj, issue, start_date, end_date, time_spent_by_user
        )
        all_timespent += time_spent
        all_skipped_timespent += skipped_time_spent
        days_spent = round1(to_working_days(time_spent))
        if issuetype == "Bug":
            all_bugs_timespent += time_spent
        else:
            all_other_timespent += time_spent
        items.append(
            {
                "category_key": category_key,
                "issuetype": issuetype,
                "key": key,
                "key_or_url": "" if show_url else key + " ",
                "summary": summary,
                "storypoints": int(storypoints),
                "days_spent": days_spent,
                "status": str(fields.status),
                "parent": fields.parent if issuetype == "Sub-task" else None,
                "raw": issue,
                "work_items": work_items,
                "by_user": by_user_for_issue,
            }
        )
        if category_key == "indeterminate":
            category_key = str(fields.status)
        if category_key in ("done", "Internal review"):
            done_sp += storypoints
        else:
            failed_sp += storypoints

    if merged_subtasks:
        items = merge_subtasks(items)
    for item in items:
        worked = format_spent_by_user(item["by_user"], 0.15) if worked_on else ""
        formatted = "{category_key:5.5} {issuetype:5.5} {days_spent}d /{storypoints:>2}sp {key_or_url:<11} {status:<16} {summary} {worked}".format(
            worked=worked, **item
        )
        formatted_list.append(formatted)

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
