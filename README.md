# LibraLens

LibraLens is a Python library providing tools for the evaluation of MARC 21 records. It supports MARC records in text and MARCXML format. Records can be evaluated independently or compared against corresponding gold records. LibraLens is designed as a toolbox: evaluation tools can be selected depending on the type of analysis to perform.

## Command Line Interface

Evaluate records from a file:

```
libralens records.xml
```

Evaluate all supported files in a directory:

```
libralens records/
```

Optionally provide corresponding gold records:

```
libralens records/ --gold gold/
```