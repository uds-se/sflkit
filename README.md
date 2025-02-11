# SFLKit: A Workbench for Statistical Fault Localization

[![Python Version](https://img.shields.io/pypi/pyversions/sflkit)](https://pypi.org/project/sflkit/)
[![GitHub release](https://img.shields.io/github/v/release/uds-se/sflkit)](https://github.com/uds-se/sflkit/releases)
[![PyPI](https://img.shields.io/pypi/v/sflkit)](https://pypi.org/project/sflkit/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/uds-se/sflkit/test-sflkit.yml?branch=main)](https://img.shields.io/github/actions/workflow/status/uds-se/sflkit/test-sflkit.yml?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/uds-se/sflkit/badge.svg?branch=main)](https://coveralls.io/github/uds-se/sflkit?branch=main)
[![Licence](https://img.shields.io/github/license/uds-se/sflkit)](https://img.shields.io/github/license/uds-se/sflkit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# The new project URL is [https://github.com/smythi93/sflkit](https://github.com/smythi93/sflkit).

SFLKit (https://dl.acm.org/doi/10.1145/3540250.3558915) is an out-of-the-box library and tool for statistical fault 
localization. Statistical fault localization aims at detecting execution features that correlate with failures, such as 
whether individual lines are part of the execution.

## Language Support

SFLKit currently supports Python 3, but we plan on releasing further language support.

## Installation

You need to navigate to the root directory of SFLKit and run
```sh
pip install sflkit
```
If you have a separate Python 2 and Python 3 on your machine, you may need to run
```sh
pip3 install sflkit
```

## Execution

To execute SFLKit, you need to create a config file that matches your needs.

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
usage: sflkit [-h] [--debug] -c CONFIG {instrumentation,analyze} ...

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
sflkit -c path/to/your/config instrument
```
to instrument the project defined by the file. 

After the instrumentation, you can run your tests or experiments. But keep in mind to preserve the `EVENTS_PATH` file 
for each failing and passing run.

If you want to analyze your runs, you need to execute
```sh
sflkit -c path/to/your/config analyze
```
which produces an output with the suggested code locations for the analysis objects and metrics defined in the config 
file.

## Citing SFLKit

You can cite SFLKit as following
```bibtex
@inproceedings{10.1145/3540250.3558915,
  author = {Smytzek, Marius and Zeller, Andreas},
  title = {SFLKit: a workbench for statistical fault localization},
  year = {2022},
  isbn = {9781450394130},
  publisher = {Association for Computing Machinery},
  address = {New York, NY, USA},
  url = {https://doi.org/10.1145/3540250.3558915},
  doi = {10.1145/3540250.3558915},
  abstract = {Statistical fault localization aims at detecting execution features that correlate with failures, such as whether individual lines are part of the execution. We introduce SFLKit, an out-of-the-box workbench for statistical fault localization. The framework provides straightforward access to the fundamental concepts of statistical fault localization. It supports five predicate types, four coverage-inspired spectra, like lines, and 44 similarity coefficients, e.g., TARANTULA or OCHIAI, for statistical program analysis.  
  SFLKit separates the execution of tests from the analysis of the results and is therefore independent of the used testing framework. It leverages program instrumentation to enable the logging of events and derives the predicates and spectra from these logs. This instrumentation allows for introducing multiple programming languages and the extension of new concepts in statistical fault localization. Currently, SFLKit supports the instrumentation of Python programs. It is highly configurable, requiring only the logging of the required events.},
  booktitle = {Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering},
  pages = {1701–1705},
  numpages = {5},
  keywords = {similarity coefficient, spectrum-based fault localization, statistical debugging, statistical fault localization},
  location = {<conf-loc>, <city>Singapore</city>, <country>Singapore</country>, </conf-loc>},
  series = {ESEC/FSE 2022}
}
```
