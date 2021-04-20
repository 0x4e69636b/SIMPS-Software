# SIMPS-Software
Software for the SIMPS ATE device.

## Python Installation
Note: The LabVIEW software is dependent on the python library for the SIMPS device. LabVIEW requires a matching architecture, so please install matching 32-bit or 64-bit versions of python and LabVIEW.
1. Download the latest Python 3.6 release: https://www.python.org/downloads/release/python-368/
2. While installing ensure that *Add Python x.x to PATH* is selected.

## Python Dependency Installation
1. As an administrator, open Command Prompt. Right click "Command Prompt" and select "Run as administrator."
2. Install with the command, `pip3 install ftd2xx`

## LabVIEW Installation
* Follow the instructions provided here: https://myapps.asu.edu/app/labview
* Run `SIMPS 2.5.vi`

## Running the Command Line Interface
Using Command Prompt (you no longer need to be an administrator), cd to the directory where you have downloaded/cloned the python files for the interface.
i.e. `cd /d "D:\ASU\Capstone\SIMPS-ATE-CLI"`

Execute the command line interface with `python simps_cli.py`

For help use `python simps_cli.py --help` and for help with a sub menu `python simps_cli.py measurement --help`
