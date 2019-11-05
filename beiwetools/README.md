Josh Barback  
barback@fas.harvard.edu  
Onnela Lab, Harvard T. H. Chan School of Public Health

___
beiwetools
===

The `beiwetools` package provides classes and functions for working with Beiwe data sets and Beiwe study configurations.  

This document provides a brief description of each sub-package, along with some background about Beiwe configuration files and raw data.

There are four sub-packages:

* `helpers`:  Functions for handling common scenarios, such as converting time formats, organizing Beiwe data files, and plotting timestamps,
* `configread`:  Tools for querying Beiwe configuration files and generating study documentation,
* `manage`:  Tools for organizing and summarizing directories of raw Beiwe data,
* `localize`:  Classes and functions for incorporating users' time zones into the analysis of processed Beiwe data.

To install this package with pip:

```bash
pip install /path/to/beiwetools
```

Example imports:

```python
import beiwetools.configread as configread
from beiwetools.helpers.time import to_timestamp
```


___
## Table of Contents
1.  [Version Notes](#version)  
2.  [Overview](#overview)  
3.  [Time Formats](#time)  
4.  [File Names & Contents](#files)  
5.  [Directory Structure](#directory)  
6.  [Variable Names](#names)  
7.  [`beiwetools.helpers`](#helpers)  
8.  [`beiwetools.configread`](#configread)  
9.  [`beiwetools.manage`](#manage)  
10.  [`beiwetools.localize`](#localize)  
11.  [Examples](#examples)  
12.  [General Cautions](#cautions)  


___
## Version Notes <a name="version"/>

This is version 0.0.1 of `beiwetools`.  This package was developed with Python 3.7.4 on PCs running Manjaro Illyria 18.0.4.

Among the package requirements, the following are not in the Python Standard Library:

* `pandas`
* `pytz`
* `seaborn`


___
## Overview <a name="overview"/>

#### Beiwe Studies
A *Beiwe study* corresponds to a collection of surveys and device settings.  These study parameters determine the app's behavior when it is installed on a user's phone, including:

* How and when surveys are delivered,
* How often data are uploaded,
* Which sensors are sampled for passive data collection.

Each Beiwe user is assigned an alphanumeric string (a *user ID*), when he or she is registered in a study.  Each Beiwe study is assigned both a hex-string identifier (*study ID*) and a human-readable name.  

Using the above identifiers, researchers can download raw user data from the Beiwe backend.  This can be done manually (e.g. from `studies.beiwe.org`) or with tools from the `mano` package.


#### Configuration Files <a name="configuration"/>
The parameters of a Beiwe study can be exported to a *configuration file* in JSON format.  Configuration file names may have the following format:

```
The_Name_of_the_Study_surveys_and_settings.json
```

Such a file contains a serialized representation all the study's **device settings**, including:

* On/off cycle periods for passive data collection,
* Text that is displayed to users,
* How and when data are uploaded to the backend.

A configuration file also contains details about the study's **surveys**, such as:

* Survey delivery schedule,
* Question types and and content,
* Branching logic (or "skip" logic) for delivery of questions.

Note that configuration files do *not* contain the following information:

* Individual user identifiers,
* Human-readable names for studies, surveys, or other objects.

In this package, lists of attributes found in Beiwe configuration files are provided in two JSON files:

```bash
/beiwetools/configread/
	study_settings.json
	survey_settings.json	
```

Note that there are three slightly different formats for configuration files:

* **MongoDB Extended JSON format.** In older Beiwe configuration files, objects are identified only with  an `_id` attribute.  Objects in these configuration files do not have a `deleted` attribute, and in some cases there may be other minor differences across attributes.
* **Current format V1.**  Since June 2018, Beiwe configuration files identify objects (such as surveys) with both an `id` (integer) and an `object_id` (hex string).  All objects have an additional Boolean attribute `deleted`.
* **Current format V2.** In 2019, the following device settings were added:
    `call_clinician_button_enabled`  
    `call_research_assistant_button_enabled`  
    `use_gps_fuzzing`  

Lastly, note that the Beiwe study identifier that appears in a configuration file may not match the study ID found elsewhere on the Beiwe backend.  (This is a concern only for study IDs.  Configuration files do appear to provide correct identifiers for surveys and questions.)

___
## Time Formats <a name="time"/>

Several time formats are used in Beiwe data and configuration files.  With few exceptions, these formats correspond to times in Coordinated Universal Time (UTC).

#### Timestamps
In raw Beiwe data, each observation is associated with a timestamp corresponding to the number of milliseconds that have elapsed since the Unix epoch, January 1, 1970 00:00:00 Coordinated Universal Time (UTC).

#### File Names
A raw Beiwe data set contains `csv` files organized according to the directory structure described in the following section.  Each file corresponds to one hour of observations.

  Each file is named  ...

#### Raw Data

column names, UTC column, filenames

#### Configuration Files
Each survey in a Beiwe study has a `timings` attribute that indicates which days and times the survey is delivered.  This attribute is a list of seven lists of integers.  For example:

```
[[],[37800],[],[37800, 50400],[],[50400],[]]
```

Position in the top list indicates day of the week, starting with Sunday.  (Note that this differs from the usual Python day order, which starts with Monday.)  Integers correspond to the user's local time, in seconds from midnight (see `helpers.time.convert_seconds()`).  In the above example, the survey is delivered at 10:30AM on Mondays & Wednesdays, and at 2:00PM on Wednesdays & Fridays.


#### Local Time
Some modules in this package report local times for various purposes.  

File names or directory names may include the researcher's local date/time, formatted as: `%Y-%m-%d_%H:%M:%S_%Z`. 

Log files may include the researcher's local date/time formatted as: `%Y-%m-%d %H:%M:%S %Z`.

User's local time

___
## File Names & Contents <a name="files"/>


___
## Directory Structure <a name = "#directory"/>
  
Raw Beiwe data may be downloaded from the backend and extracted to a directory chosen by the researcher.  The `beiwetools` package assumes the following directory structure:

```
<raw data directory>/

	<Beiwe User ID #1>/
		identifiers/
		<passive data stream #1>/
		<passive data stream #2>/
		.
		.
		.
		audio/
		tracking/

	<Beiwe User ID #2>/
		identifiers/
		<passive data stream #1>/
		<passive data stream #2>/
		.
		.
		.
		audio/
		tracking/		
	
	.
	.
	.
```

Note that `<raw data directory>` is typically a location chosen by the researcher.  The remainder of the directory structure is determined by the study's specific data collection settings.

Each user's data are found in a folder labeled with the user's Beiwe ID, which is an alphanumeric string.  Multiple users enrolled in the same Beiwe study may have data folders in the same raw data directory.

Each user's data directory will include a folder labeled `identifiers`; this contains files with records of the user's device.  Additional passive data folder names may be `accelerometer`, `calls`, `gps`, etc.

A user's data directory will also contain one folder for each type of survey that has been delivered.  Possible folder names are:


___
## Variable Names <a name="names"/>


In the `beiwetools` package, some commonly used variable names are the following:

* `raw_dir`: Path to the raw data directory chosen by the researcher, described in the previous section.
*
*
*

user ID
study ID

time

___
## `beiwetools.helpers` <a name="helpers"/>

This sub-package provides classes and functions that are used throughout `beiwetools` and also by Beiwe reporting packages (`accrep`, 'gpsrep', `survrep`).  Below is an overview of each module.

#### `classes` & `functions`
These modules provide general-purpose tools for tasks that often arise when working with Beiwe configurations and raw data.  Commonly used functions include those for performing basic list operations and for reading/writing JSON files as ordered dictionaries.  Commonly used classes include `Timer` (for timing data processing tasks) and `Summary` (for generating human-readable summaries of Beiwe objects).




#### `colors`
A few functions for generating Color Brewer palettes.

#### `plot`
	* Generating visual and numerical summaries of raw data,




#### `process`
The tools in this module assume the Beiwe [file naming conventions](#files) and [directory structure](#directory) that are described in this document.  

#### `time` & `time_constants`
The `time` module provides functions for working with the various [time formats](#time) found in Beiwe data.  Commonly used timezones and date-time formats are found in `time_constants`.








___
## `beiwetools.configread` <a name="configread"/>

The `configread` sub-package provides classes for representing information in Beiwe configuration files, with methods for generating documentation.  These modules have been tested on 32 configuration files from nine Beiwe studies.

Review [this section](#configuration) for information about configuration files.

#### Study Attributes
To ensure compatibility across formats, the `configread` package looks for all known study attributes, regardless of file format.  Therefore, due to differences across configuration file formats, it is not unusual to see many missing values.

Documented study attributes can be found in `study_settings.json` and `survey_settings.json`.  Any undocumented attributes are logged whenever a `BeiweConfig` object is instantiated.

#### Identifiers
The `configread` package attaches identifiers to each Beiwe survey and question object.  These correspond to the unique identifiers found in raw survey response data, and can be used to query the content of surveys and questions.  
 
Each identifier is either the `object_id` or the `_id` assigned to the survey or question, depending on the format of the configuration file.

#### Study Documentation
Use `BeiweConfig.export()` to generate configuration documentation.  Documentation from a `BeiweConfig` instance is organized as follows:

```
configuration_documentation_from_<local time>/
	The_Name_of_the_Study/

		overview.txt
		warnings.txt
		
		records/			
			paths.json
			raw.json
			names.json

		settings/					
			general_settings.txt
			display_settings.txt
			passive_data_settings.txt
						
		audio_surveys/
			<Name of Audio Survey #1>.txt
			<Name of Audio Survey #2>.txt		
			.
			.
			.

		tracking_surveys/
			<Name of Tracking Survey #1>.txt
			<Name of Tracking Survey #2>.txt		
			.
			.
			.
			
		other_surveys/
			<Name of Other Survey #1>.txt
			<Name of Other Survey #2>.txt		
			.
			.
			.
```

The file `warnings.txt` provides a record of any undocumented settings or objects found in the configuration file. A common undocumented object is the "dummy" survey type, which is probably assigned to surveys that have been deleted.

The `records` folder contains everything needed to recreate an identical BeiweConfig instance.  To do this, either (1) provide paths to `raw.json` and `names.json` as input, or (2) just provide a path to the folder labeled with the name of the study.  Note that `raw.json` is just a "pretty-printed" copy of the original Beiwe configuration file.

Other files with the `.txt` extension contain human-readable summaries of the contents of the Beiwe configuration.  In these files, an attribute that is "Not found" probably belongs to a different format of configuration file.  It is normal to see "Not found" in many places.

#### Naming
By default, `configread` assigns human-readable names to each study survey and question.  Names are of the form `Survey_01`, `Survey_01_Question_01`, etc.  These names are assigned in the order in which objects appear in the corresponding JSON file, and may not agree with names found on the Beiwe backend.

For convenience, it may be desirable to assign a descriptive name to each study survey and survey item.  Names can be exported and reloaded in the future.  See `configread_example.ipynb` for sample code.

#### Scoring
In Beiwe questionnaires (called "tracking surveys"), responses to checkbox and radio button items are assigned a numeric score.  This score is the zero-based index of the response in the corresponding list of answers.  For example, if possible answers are `['High', ''Medium', 'Low']` then the assigned scores are 0, 1, 2.

#### Limitations & Cautions
This sub-package does not parse branching logic settings used for conditional delivery of tracking survey items.  Use `TrackingQuestion.logic` to view a question's logic configuration.

Note that only tracking surveys and audio surveys are represented by dedicated classes.  Other survey types (e.g. image surveys) are represented with the generic BeiweSurvey class.

Lastly, note that comparison of `configread` objects is intended to be somewhat flexible.  This is to accommodate the possibility that the same study configuration may be serialized in different formats.  Therefore, some caution should be used when checking equality.


___
## `beiwetools.manage` <a name="manage"/>


Specifically for working locally (e.g. on a PC) with raw Beiwe data that has been downloaded from the backend.

* Managing directories of raw data,


This sub-package provides classes and functions for managing raw Beiwe data.  These tools are intended for use when processing data locally, e.g. on a PC with data that have been downloaded from the Beiwe backend.


___
## `beiwetools.localize` <a name="localize"/>

This sub-package provides tools for localizing processed Beiwe data to the time zone of the user.

#### `classes`

The `Localize` class identifies timezones for timestamps, given a dictionary of a user's timezone transitions generated with the `gpsrep` package.  

The `ProcData` class provides a framework for partitioning processed data into 24-hour periods that are consistent with the user's local time.  Variables of interest can be "loaded" into a `ProcData` object as 2-D arrays.  Arrays of processed data can then be exported to text files or reshaped into a feature matrix.

#### `plot`

This module provides functions for generating simple visualizations of longitudinal data from `ProcData` objects.


#### `fitabase`

Some functions for loading fitabase data sets into a `ProcData` object.


___
## Examples <a name="examples"/>

 * `configread_example.ipynb`

Code examples (iPython notebooks and Python scripts) are located in the `examples` folder.


___
## General Cautions <a name="cautions"/>

#### Compatibility
The modules in this package were written with the intention of preserving compatibility with previous versions of Python.  For example, it is generally desirable to preserve key insertion order when reading JSON files into dictionaries.  Since Python 3.6, dictionaries do preserve insertion order.  However, for compatibility with previous versions, we use ordered dictionaries (`collections.OrderedDict`) instead.

Note that sub-packages are currently collected in a [native namespace package](https://packaging.python.org/guides/packaging-namespace-packages/#native-namespace-packages), which is supported only by Python 3.3 and later.


