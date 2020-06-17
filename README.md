# Tools for Scrum Masters


## Description

This repository contains a set of tools useful for SCRUM masters:


## Tools

### jisprint

Jisprint let's you extract sprint informations from JIRA, which is particularily useful for retrospectives.
The tool takes the JIRA sprint number in parameter, which you can find in the URL of a sprint report, in JIRA.

Before running the tool, make sure your credentials are present in the [~/.netrc file](https://jira.readthedocs.io/en/master/examples.html#authentication):

```machine THE_JIRA_HOST login YOUR_USERNANE password YOUR_PASSWORD```

Exemple usage:

```venv/bin/python jisprint/get_single_sprint.py 1128```


## Contributing

Let's discuss new ideas and improvements together, in real life.


# Origin

These tools where originally written by Guillaume Beraudo.
