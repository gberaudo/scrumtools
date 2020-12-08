# Tools for Scrum Masters

## Description

This repository contains a set of tools useful for SCRUM masters:

## Setup

### Authentication

Before running the tool, make sure your credentials are present in the [~/.netrc file](https://jira.readthedocs.io/en/master/examples.html#authentication).
Example:

```machine jira.camptocamp.com login YOUR_USERNANE password YOUR_PASSWORD```

### Installation

Install it (`$HOME/.local/bin/` should be in your `PATH`):

```bash
python3 -m pip install --user --editable=. --no-use-pep517
```

## Tools

### jisprint/get-board-sprints

Jisprint get-board-sprints will list the sprints of the board, allowing you to quickly find sprint ids.
For it to work you need to pass the board id.

- getting the board id

The board id is the parameter called `rapidview` in the sprint or report URLs.
Example:
`https://jira.camptocamp.com/secure/RapidBoard.jspa?rapidView=583`

- usage

```get-board-sprints --board 583```

or, if you are using a `.scrum` file: ```get-board-sprints```


### .scrum file

A .scrum file is placed at the root of a project. It contains configuration, like this:

```ini
board=583
```

### jisprint/get-single-sprint

Jisprint get-single-sprint let's you extract sprint informations from JIRA, which is particularily useful for retrospectives.
It displays the list of cards, with their spent time and number of storypoints.
Only the worklogs started during the sprint span are considered.
A sprint starts at 00:00:00 the day of the planning and finishes at 23:59:59 the day before the demo.

- getting the sprint id

The tool takes the JIRA sprint number in parameter, which you can find in the URL of a sprint report, in JIRA.
Example:

`https://jira.camptocamp.com/secure/RapidBoard.jspa?rapidView=583&projectKey=GSNGM&view=reporting&chart=sprintRetrospective&sprint=1128`
=> the sprint ID id 1128

Exemple of call:

```get-single-sprint --sprint 1128```

or, if you are using a `.scrum` file: ```get-single-sprint```

### jisprint/get-epic-info

Jisprint get-epic-info let's you get infos from a JIRA epic. It displays information about cards sharing a particular epic.
It is placed in the jisprint directory for convenience.

Example:

get-epic-info GSDESCARTE-2

### jisprint/get-project-info

Jisprint get-project-info let's you get infos from a JIRA project. It displays information about cards parts of a particular project.
It is placed in the jisprint directory for convenience.

Example:

get-project-info MY_SUPER_PROJECT

## Contributing

Let's discuss new ideas and improvements together, in real life.

## Origin

These tools where originally written by Guillaume Beraudo.
