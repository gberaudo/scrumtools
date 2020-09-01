from setuptools import setup

setup(
    name="scrumtools",
    install_requires=["jira", "python-dateutil"],
    entry_points={"console_scripts": [
        "get-single-sprint = jisprint.get_single_sprint:main",
        "get-board-sprints = jisprint.get_board_sprints:main"
    ]},
)
