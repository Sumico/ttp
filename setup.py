"""setup.py file."""
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

__author__ = "Denis Mulyalin <d.mulyalin@gmail.com>"

setup(
    name="ttp",
    version="0.0.3",
    author="Denis Mulyalin",
    author_email="d.mulyalin@gmail.com",
    description="Template Text Parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmulyalin/ttp",
    packages=[
        "ttp", 
        "ttp.functions",
        "ttp.functions.match",
        "ttp.functions.group",
        "ttp.functions.input",
        "ttp.functions.output",
        "ttp.functions.variable",
        "ttp.templates"
    ],
    #packages=["ttp"],
    include_package_data=True,
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        'console_scripts': ['ttp=ttp.ttp:cli_tool'],
    }
)

"""
to install without making egg:
python3 -m pip install .
"""