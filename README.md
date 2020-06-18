# Tools for Scrum Masters


## Description

This repository contains a set of tools useful for SCRUM masters:


## Tools

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

- setting authentication

Before running the tool, make sure your credentials are present in the [~/.netrc file](https://jira.readthedocs.io/en/master/examples.html#authentication).
Example:

```machine jira.camptocamp.com login YOUR_USERNANE password YOUR_PASSWORD```

Install it (`$HOME/.local/bin/` should be in your `PATH`):

```python3 -m pip install --user --editable=.```

Exemple of call:

```get-single-sprint 1128```


## Contributing

Let's discuss new ideas and improvements together, in real life.


# Origin

These tools where originally written by Guillaume Beraudo.
