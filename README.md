# SFLKit: A Workbench for Statistical Fault Localization

[![Python Version](https://img.shields.io/pypi/pyversions/sflkit)](https://pypi.org/project/sflkit/)
[![GitHub release](https://img.shields.io/github/v/release/uds-se/sflkit)](https://img.shields.io/github/v/release/uds-se/sflkit)
[![PyPI](https://img.shields.io/pypi/v/sflkit)](https://pypi.org/project/sflkit/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/uds-se/sflkit/test-sflkit.yml?branch=main)](https://img.shields.io/github/actions/workflow/status/uds-se/sflkit/test-sflkit.yml?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/uds-se/sflkit/badge.svg?branch=main)](https://coveralls.io/github/uds-se/sflkit?branch=main)
[![Licence](https://img.shields.io/github/license/uds-se/sflkit)](https://img.shields.io/github/license/uds-se/sflkit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

SFLKit (https://dl.acm.org/doi/10.1145/3540250.3558915) is an out-of-the-box library and tool for statistical fault 
localization. Statistical fault localization aims at detecting execution features that correlate with failures, such as 
whether individual lines are part of the execution.

## Language Support

SFLKit supports currently Python 3 but we plan on releasing further language support.

## Installation

You need to navigate to the root directory of SFLKit and run
```sh
pip install .
```
If you have a separate Python 2 and Python 3 on your machine you may need to run
```sh
pip3 install .
```

## Execution

To execute SFLKit you need to create a config file matching your needs.

### Config

```ìni
[target]
path=/path/to/the/subject
language=Python|C                       ; The programming language used

[events]
events=Event(,Event)*                   ; The events to investigate, overwritten by predicates.
predicates=Predicate(,Pridcate)*        ; The predicates to investigate, overwrites events.
metrics=Metric(,Metric)*                ; The metrics used for investigation
passing=/path(,path)*                   ; The event files of passing runs, if a dir is provided
                                        ; all files inside the tree will be treated as event files
failing=/path(,path)*                   ; The event files of failing runs, if a dir is provided
                                        ; all files inside the tree will be treated as event files

[instrumentation]
path=/path/to/the/instrumented/subject
exclude=file(,file)*                    ; Files to exclude from the instrumentation, should be a python re pattern

[test]
runner=TestRunner                       ; The testrunner class, None if no run needed
```

This is the specification of the config file.

### Usage

The general usage of SFLKit is
```
usage: SFLKit [-h] [--debug] -c CONFIG {instrumentation,analyze} ...

A workbench for statistical fault localization python programs and in the future other programs.

optional arguments:
  -h, --help            show this help message and exit
  --debug               the debug flag to activate debug information
  -c CONFIG, --config CONFIG
                        path to the config file

command:
  The framework allows for the execution of various commands.

  {instrumentation,analyze}
                        the command to execute
    instrumentation     execute the instrumentation of subject
    analyze             execute the analysis of the collected predicates
```

If you have adopted a config file for your investigations you need to execute
```sh
python3 sfl.py -c path/to/your/config instrument
```
to instrument the file. 

After the instrumentation, you can run your tests or experiments. But keep in mind to preserve the `EVENTS_PATH` file 
for each failing and passing run.

If you want to analyze your runs you need to execute
```sh
python3 sfl.py -c path/to/your/config analyze
```
which produces an output with the suggested code locations for the analysis objects and metrics defined in the config 
file.
