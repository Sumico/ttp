Overview
=========

TTP is a Python module that allows parsing of semi-structured text data using templates mainly rallying on Python built-in regular expression module and XML Etree to structure templates. TTP was mainly developed to enable programmatic access to data produced by CLI of networking devices, however, it can be used to parse any semi-structured text that contains distinctive repetition patterns.

In the simples case ttp takes two files as an input - data that needs to be parsed and parsing template, returning results structure that contains extracted information.

Same data can be parsed by several templates producing results accordingly, templates are easy to create and users encouraged to write their own ttp templates, in addition ttp shipped with a set of template examples applicable for parsing CLI output of major network equipment.

Motivation
----------

While networking devices continue to develop API capabilities there is a huge footprint of legacy and not-so devices exists in the field, these devices are lacking of any well developed API to retrieve structured data, the closest they can get is SNMP or CLI text output. Moreover, even if some devices have API and capable of representing their configuration or state data in the form that can be consumed programmatically, in certain cases the amount of work that needs to be done to make use of these capabilities outweighs the benefits or value of produced results.