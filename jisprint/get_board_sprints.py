import argparse
import logging

from .util import get_jiraobj, read_board_from_scrum_file

def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="JIRA board tool")
    parser.add_argument("--board", type=int, default=0, help="the board id.")
    parser.add_argument("--host", type=str, default="camptocamp.atlassian.net", help="the JIRA server host")

    args = parser.parse_args()

    jiraobj = get_jiraobj(args.host)

    board_id = args.board
    if board_id == 0:
        board_id = read_board_from_scrum_file()

    # using maxResults=0 enters the batch mode which will fetch all results
    sprints = jiraobj.sprints(board_id, maxResults=0, state="active,closed")
    for s in sprints:
        print(f"{s.name} {s.id} ({s.state})")


if __name__ == "__main__":
    main()
