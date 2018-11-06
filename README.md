# Axway API Gateway Deployment Package JavaScript Filter Checker

## Overview
This Python script will parse the JavaScript Filters from a PrimaryStore XML file from an Axway API Gateway Deployment Package (FED) to validate that variables are declared as local using the 'var' qualifier.

### Background
Variables in JavaScript Filters not declared as local can lead to unexpected behaviors like swapping data across requests, and memory leaks in the API Gateway JVM process.

## Required Python Modules

### BeautifulSoup 4
BeautifulSoup is used to parse the XML in the PrimaryStore file.

For documentation on BeautifulSoup, please consult: [https://www.crummy.com/software/BeautifulSoup/bs4/doc/]

### pyjsparser
Not wanting to re-invent the wheel on JavaScript code parsing, the pyjsparse module is used to parse the JavaScript code.  

For information on this module, please consult: [https://github.com/PiotrDabkowski/pyjsparser]

## Executing parseJScript.py
The script takes the following options:
```
Options:
  -h, --help            show this help message and exit
  -f PRIMARY_STORE, --file=PRIMARY_STORE
                        PrimaryStore file name
  -e ENGINE_NAME, --engine=ENGINE_NAM
                        JavaScript engine name
  -l LOGLEVEL, --log=LOGLEVEL
                        Logging level
```

If the PrimaryStore file isn't specified, then the script looks in its directory for the pattern PrimaryStorey*.xml.  Must only be one file matching that pattern.

Engine name defaults to 'nashorn' since this was developed and tested for API Gateway v7.5.3.

Log level defaults to INFO if not specified.  Use DEBUG to display messages during parsing.  Use CRITICAL if you need to see the resulting dictionary from JavaScript parsing.

## Development and Test Platform
This script was developed and tested using Python v2.7.15.  The version of the API Gateway FED is v7.5.3.  The script was developed on macOS, so it will work with Linux based platforms.  It has not been tested on Windows (and probably won't work due to file pathing).

## None Issues
This script does not deal with nested functions, and may show them as problems.
