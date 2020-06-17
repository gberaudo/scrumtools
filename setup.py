from setuptools import setup

setup(
    name="scrumtools",
    entry_points={"console_scripts": ["get-single-sprint = jisprint.get_single_sprint:main"]},
)
