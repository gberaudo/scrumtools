import argparse
import logging

import dateutil.parser
from jira import JIRA

import os.path


def guess_board_id(jiraobj):
    if not os.path.exists(".scrum"):
        raise Exception("Could not guess the sprint id. No .scrum file found.")
    with open(".scrum", "r") as f:
        for line in f:
            name, var = line.partition("=")[::2]
            if name.strip() == "board":
                return var.strip()
        raise Exception("No board id found in the .scrum file")


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA board tool")
    parser.add_argument("--board", type=int, default=0, help="the board id.")
    parser.add_argument("--host", type=str, default="jira.camptocamp.com", help="the JIRA server host")

    args = parser.parse_args()

    jiraobj = JIRA({"server": "https://" + args.host})

    board_id = args.board
    if board_id == 0:
        board_id = guess_board_id(jiraobj)

    sprints = jiraobj.sprints(board_id)
    for s in sprints:
        if s.state not in ("FUTURE"):
            print("%s %s (%s)" % (s.name, s.id, s.state))


if __name__ == "__main__":
    main()
