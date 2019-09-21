Overview
=========

TTP is a Python module that allows parsing of semi-structured text data using templates structured in certain format. TTP was developed to enable programmatic access to data produced by CLI of networking devices, however, it can be used to parse any semi-structured text that contains distinctive repetition patterns.

In the simplest case ttp takes two files as an input - data that needs to be parsed and parsing template and returns results structure with extracted information.

Same data can be parsed by several templates producing results accordingly, templates are easy to create and users encouraged to write their own ttp templates.

Motivation
----------

While networking devices continue to develop API capabilities there is a big footprint of legacy and not-so devices in the field, these devices are lacking of any well developed API to retrieve structured data, the closest they can get is SNMP and CLI text output. Moreover, even if some devices have API and capable of representing their configuration or state data in the form that can be consumed programmatically, in certain cases, the amount of work that needs to be done to make use of these capabilities outweighs the benefits or value of produced results.

There are a number of tools available to parse text data, however, author of TTP believes that parsing data is only part of the work flow, where the ultimate goal is to make use of the data. Say we have configuration files and we want to create a report of all IP addresses configured on devices together with VRFs and interface descriptions, report should have csv format. To do that we have (1) collect data from various inputs and may be sort or prepare it, (2) parse that data, (3) format it in certain way and (4) save it somewhere or pass to other program(s). TTP has built-in capabilities to address all of the steps above to produce desired outcome.

One more problem - hierarchical data, configuration can be structured using hierarchical patterns, sometimes quite difficult to parse, however, ttp can help to address that problem using groups, allowing to define arbitrary, nested structures of lists and dictionaries.