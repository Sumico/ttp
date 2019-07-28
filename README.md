# Template Text Parser

TTP is a Python module that allows parsing of semi-structured text data using templates mainly ralying on Python built-in regular expression module and XML Etree to structure templates. TTP was mainly developed to enable programmatic access to data produced by CLI of networking devices, however, it can be used to parse any semi-structured text that contains distinctive repetition patterns.

In the simples case ttp takes two files as an input - data that needs to be parsed and parsing template, returning results structure that contains extracted information.

Same data can be parsed by several templates producing results accordingly, templates are easy to create an users encoureged to write their own ttp templates, in addition ttp shipped with a set of template examples applicable for parsing CLI output of major network equipment.