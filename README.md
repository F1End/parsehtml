## parsehtml

## Contents
- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)

## Description
Part of [Wartracker project](https://github.com/users/F1End/projects/1/views/1?pane=info).

This script parses html content into a single csv row (as an step before further processing).
The input to the script is saved html content from (local) file system, and not direct web url.
Currently configured to parse losses from Oryx's [Ukrainian](https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html) and [Russian](https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html) losses pages concerning the Russo-Ukrainian war.

Long-term plans include extending coverage to other resources, e.g. pledges and other loss documenting sites.

## Requirements
The script uses python 3.13, but likely will work with most earlier versions after 3.8

The external library requirements are BeautifulSoup4 and Pandas.

## Installation

1. Git clone repo
2. Install requirements (and create venv if needed)
3. Run via command line

## Usage

Although there is one primary module for parsing losses, due to a slight difference between the two pages a different cutoff (when the script stops running) is specified during parsing. As a result, two separate python files are present for unning the parsing. Apart form that, they use the same logic for the interface and also the parsing itself.
Command:
<your pythin bin or exe path> --file <path to html file> --output_file <path and name of output csv>


**For Ukrainian losses**:
File:

"parse_ukr_losses.py"

Sample command:

python parse_ukr_losses.py  --file 2025-04-21_attack-on-europe-documenting-ukrainian.html --output_file 025-04-21_attack-on-europe-documenting-ukrainian_parsed.csv


**For Russian losses**:
File:

"parse_ru_losses.py"

Sample command:

python parse_ru_losses.py  --file 2025-04-21_attack-on-europe-documenting-ukrainian.html --output_file 025-04-21_attack-on-europe-documenting-ukrainian_parsed.csv
