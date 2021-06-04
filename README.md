# ITS Data Sandbox

This repository contains information on accessing complete datasets from the United States Department of Transportation (USDOT) Joint Program Office (JPO) data program's ITS Data Sandbox. It is meant to propose a data folder hierarchy to structure the processed data ingested from the Connected Vehicles (CV) Pilot programs, Work Zone Data Exchange (WZDx) programs, and other future streaming data sources, as well as direct users to related tools and resources.

## Table of Contents

* [Background](#backgound)
* [Data Types](#data-types)
	* [CV Pilot Data](#cv-pilot-data)
	* [Work Zone Data Exchange Feed Data](#wzdx-feed-data)
* [Accessing the data](#accessing-the-data)
	* [Web Interface](#web-interface)
	* [Amazon Command Line Interface](#aws-cli)
	* [Sandbox Exporter](#sandbox-exporter)
* [Get Involved](#get-involved)
* [Related ITS JPO Projects](#related-its-jpo-projects)

## Background

The ITS Data Sandbox are a collection of public Amazon Simple Storage Service (S3) buckets maintained by JPO's ITS DataHub team and came out of the desire to make raw research data with evolving data schema to be availale in near-real-time. S3 buckets provide an alternative that is similar to traversing a directory structure. The intention of the hierarchy is to:

- Provide a consistent structure within a pilot program
- Be easily understood by a human traversing the directories
- Be structured sufficiently so third parties can build software applications using the data
- Be flexible enough to capture different data types.

The expectation is that different data types will lend themselves to different directory hierarchies. In addition, within each sandbox, each data producer may choose to organize their data differently (e.g., the CV pilot sites may have compelling reasons to organize the data in different hierarchies for the same data type). The below hierarchy is intended for processed data from the Wyoming and Tampa CV Pilot sites, and for data feeds compliant with the WZDx specification.

## Data Types

There are currently three data sandboxes available:
- [CV Pilot Data Sandbox](#folder-hierarchy-cv-pilot-data)
- [Work Zone Raw Data Sandbox](#folder-hierarchy-wzdx-raw-data)
- [Work Zone Data Sandbox](#folder-hierarchy-wzdx-semi-processed-data)

### CV Pilot Data
CV Pilot data are located in the `usdot-its-cvpilot-public-data` s3 bucket.

An overview of open data resources related to the Connected Vehicle Pilot can be found in this [data story](https://data.transportation.gov/stories/s/Connected-Vehicle-Pilot-Sandbox/hr8h-ufhq). Please see change notes relating to any major changes to the data at the [cv_pilot_ingest GitHub repository wiki page](https://github.com/usdot-its-jpo-data-portal/cv_pilot_ingest/wiki/ITS-CV-Pilot-Sandbox-Data-Change-Notes) and consult our [log of known data pipeline downtime and caveats](https://github.com/usdot-its-jpo-data-portal/sandbox/wiki/ITS-CV-Pilot-Data-Sandbox-Known-Data-Gaps-and-Caveats) prior to using the data. Detailed data dictionaries and documentations for the data from each pilot site can be found in their respective folders in the [doc](doc/) folder of this repository. Sample records can be downloaded from the CVP Sandbox [Web Interface](#web-interface) directly or be downloaded from the [sample](sample/) folder of this repository.

#### Folder Hierarchy: CV Pilot Data
CV Pilot data is currently stored in the following folder hierarchy based on when the data is generated:

`{Source_Name}/{Data_Type}/{Year}/{Month}/{Day}/{Hour}`

* `{Source_Name}`: The data producer of the pilot. Acceptable values: `wydot`, `wydot_backup`, `thea`, `nycdot`.
* `{Data_Type}`: The message type of the data. Acceptable values: `BSM`, `TIM`, `SPAT`, `EVENT`. `SPAT` is only available when the `Source_Name` is `thea`. `EVENT` is only available when the `Source_Name` is `nycdot`.
* `{Year}`: Four-digit year value based on the `metadata.recordGeneratedAt` field in the record (e.g., `2019`). Based on UTC time. When `Source_Name` is `nycdot`, the year value is based on the `eventHeader.eventTimeBin` field in the record, which uses the NYC (EST/EDT) time zones.
* `{Month}`, `{Day}`, `{Hour}`: Two-digit month/day/hour value based on the `metadata.recordGeneratedAt` field in the record(e.g., `01`). Based on UTC military time. When `Source_Name` is `nycdot`, the month, day, and hour value is based on the `eventHeader.eventTimeBin` field in the record, with the day being day-of-week bins (`MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN`, `NA`) and hour being time-of-day bins (`AM`, `PM`, `MD`, `EV`, `NT`, `NA`). Records are assigned to the day-of-week and time-of-day bins based on the NYC (EST/EDT) time zones.

Files generated after January 18, 2018 are newline JSON files containing multiple messages. Data generated prior to that contains one message per file. 

#### Additional Resources

We included basic tutorials on how to access the [WYDOT](example/accessing_wydot.ipynb) and [NYCDOT](example/accessing_nycdot_data.ipynb) CVP data in Python Jupyter notebooks in this repository. Note that analysis of the data can be done by almost any programming langauge - Python was just selected for this example due to its ease of use and popularity.

Additional information about CV data is available at:

- [ITS JPO Connected Vehicles (CV) Pilot Deployment Program](https://www.its.dot.gov/pilots/cv_pilot_plan.htm)-  The pilot deployments are expected to integrate connected vehicle research concepts into practical and effective elements, enhancing existing operational capabilities.
- [J2735 Standard](http://standards.sae.org/j2735_201603/) - Data standard for CV data
- [General CV information: Vehicle Based Data and Availability](https://www.its.dot.gov/itspac/october2012/PDF/data_availability.pdf) - General introduction slides on CV data

### WZDx Feed Data

Raw WZDx data are located in the `usdot-its-workzone-raw-public-data` S3 bucket.
Semi-processed WZDx data are located in the `usdot-its-workzone-public-data` S3 bucket.

Feeds are ingested and archived into the [ITS Work Zone Raw Data Sandbox](http://usdot-its-workzone-raw-public-data.s3.amazonaws.com/index.html) and [ITS Work Zone Data Sandbox](http://usdot-its-workzone-public-data.s3.amazonaws.com/index.html) using code in the [wzdx_sandbox](https://github.com/usdot-its-jpo-data-portal/wzdx_sandbox) GitHub repository. Users can check whether or not a WZDx feed is being ingested into the sandbox by checking the [WZDx Feed Registry](https://datahub.transportation.gov/d/69qe-yiui), and new WZDx feeds will be added to the feed registry as they become available.

Please browse our [WZDx data story](https://datahub.transportation.gov/stories/s/Work-Zone-Data-Initiative-Partnership/jixs-h7uw/) for an overview of resources related to the Work Zone Data Exchange Feed Registry and Archive. Additional information about the WZDx specifications is available at the [WZDx Specification GitHub repository](https://github.com/usdot-jpo-ode/wzdx).

#### Folder Hierarchy: WZDx Raw Data
Raw archives of the live WZDx feeds in the feed registry are currently stored using the following folder hierarchy:

`state={state}/feedName={feedName}/year={year}/month={month}/{feedName}_{timeRetrieved}`

* `{state}`: The US state where the WZDx feed is from (e.g., `arizona`). Based on the metadata of the feed in the WZDx Feed Registry
* `{feedName}`: Name of the feed as designated by ITS DataHub when the feed is added to the registry (e.g., `mcdot`). Based on the metadata of the feed in the WZDx Feed Registry
* `{year}`: Four-digit year value based on the timeStampUpdate field in the feed's header at time of ingestion (e.g., `2019`). Based on local time at work zone location.
* `{month}`: Two-digit month value based on the timeStampUpdate field in the feed's header at time of ingestion (e.g., `01`). Based on local time at work zone location.
* `{timeRetrieved}`: UTC timestamp of when the ingestor retrieved the data from the feed. (e.g. `2019-12-03 01:10:42.551287`).

Each file is a snapshot of a particular WZDx feed at a particular point in time.

#### Folder Hierarchy: WZDx Semi-Processed Data
Semi-processed archives of the live WZDx feeds in the feed registry are currently stored using the following folder hierarchy:

`state={state}/feedName={feedName}/year={year}/month={month}/{identifier}_{beginLocation_roadDirection}_{year}{month}_v{version}.txt`

* `{state}`: The US state where the WZDx feed is from (e.g., `arizona`). Based on the metadata of the feed in the WZDx Feed Registry
* `{feedName}`: Name of the feed as designated by ITS DataHub when the feed is added to the registry (e.g., `mcdot`). Based on the metadata of the feed in the WZDx Feed Registry
* `{year}`: Four-digit year value based on the timeStampUpdate field in the feed's header at time of ingestion (e.g., `2019`). Based on local time at work zone location.
* `{month}`: Two-digit month value based on the timeStampUpdate field in the feed's header at time of ingestion (e.g., `01`). Based on local time at work zone location.
* `{identifier}`: Identifier of a work zone, based on the identifier field in the WZDx Common Core Data (e.g. `az511.gov.11122`).
* `{beginLocation_roadDirection}`: The designated direction of the road that is the start of the work zone activity (e.g., `westbound`). Based on the roadDirection field of the BeginLocation data frame.
* `{version}`: The WZDx version number that was used to create the file (e.g., `1`). Based on the metadata of the feed in the WZDx Feed Registry.

Each file is a newline JSON file containing the work zone statuses for a particular work zone for the month. The first and most recent status retrieved for the month is always archived, as are statuses flanking any detected change. At least one status is also archived for each day even if the status of the work zone has not changed.

## Accessing the Data

There are various ways to access the full datasets on ITS Data Sandbox: interactively through the [web interface](#web-interface) of each sandbox, or programmatically using the [Amazon Command Line Interface (CLI)](#aws-cli) or our [Sandbox Exporter](#sandbox-exporter) Python package. At this time, the Sandbox Exporter Python package can only be used to query data from WYDOT and THEA.

### Web Interface
One Web Interface is available for each data sandbox and allows users to browse through the sandbox's folder structure and click to download individual batched data files. The web interface for each data sandbox are available at `http://{bucket-name}.s3.amazonaws.com/index.html`. For your convenience, we have linked them here:

- [Connected Vehicle (CV) Pilot Data Sandbox](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html)
- [Work Zone Raw Data Sandbox](http://usdot-its-workzone-raw-public-data.s3.amazonaws.com/index.html)
- [Work Zone Data Sandbox](http://usdot-its-workzone-public-data.s3.amazonaws.com/index.html)

### AWS CLI

#### Prerequisites for using AWS CLI

1) Have your own Free Amazon Web Services account.
	- Create one at http://aws.amazon.com
2) Obtain Access Keys:
	- On your Amazon account, go to your profile (at the top right)
	- My Security Credentials > Access Keys > Create New Access Key
	- Record the Access Key ID and Secret Access Key ID (you will need them in step 4)
3) Have Amazon Web Services Command Line Interface (AWS CLI) installed on your computer.
	- Installation options can be found at http://aws.amazon.com/cli
	- To run AWS CLI on Windows, navigate to C:\Program Files\Amazon\ and run "aws
	 --version" to confirm that the program is installed.  This should return the version number of aws that you are running.
4) Run the following command through AWS CLI:
	```
	aws configure
	```
	and enter the following:

	* Access Key (from step 2)
	* Secret Access Key (from step 2)
	* Default region name (us-east-1)
	* Default output format (ex: json)

#### Accessing files through AWS CLI

Now go to your command window. As mentioned previously, the name of the public data sandbox buckets are:

 * CV Pilot Data Sandbox: usdot-its-cvpilot-public-data 
 * Work Zone Raw Data Sandbox: usdot-its-workzone-raw-public-data 
 * Work Zone Data Sandbox: usdot-its-workzone-public-data 

Run the following to check access:
```
aws s3 ls s3://{bucket name}/ --recursive --human-readable --summarize --profile {profile_name}
```

For Example:
```
aws s3 ls s3://usdot-its-cvpilot-public-data/ --recursive --human-readable --summarize --profile default
```

#### Downloading from S3

To download all data from the S3 Bucket, enter the following command:

```
aws s3 cp s3://{bucketname}/ {local_directory} --recursive
```

For example, to download all BSM data from 2017:
```
aws s3 cp s3://usdot-its-cvpilot-public-data/wydot/BSM/2017/ . --recursive
```

To limit the data being dowloaded you can use AWS CLI's filtering which is detailed here: http://docs.aws.amazon.com/cli/latest/reference/s3/#use-of-exclude-and-include-filters.

### Sandbox Exporter

You can also download data generated between a specified date range into larger merged CSV or JSON file(s) by using our Sandbox Exporter Python package. Please refer to the README at our [sandbox_exporter](https://github.com/usdot-its-jpo-data-portal/sandbox_exporter) GitHub repository. The Sandbox Exporter currently only works for CV Pilot data and not for the WZDx data.

## Related ITS JPO Projects

- [ITS DataHub](https://www.its.dot.gov/data/) - ITS JPO site which allows users to search for open data from ITS JPO funded research projects.
- [Operational Data Environment (ODE)](https://github.com/usdot-jpo-ode/jpo-ode) - Open-source tool from ITS JPO that is used to collect and process CV data in near real time, and route it to other data repositories, including the Amazon S3 bucket.  
- [Privacy Module](https://github.com/usdot-jpo-ode/jpo-cvdp) - Open-source module from ITS JPO that is used to sanitize the data to ensure no personal information is shared with the public.  
- [Secure Data Commons(SDC)](https://its.dot.gov/data/secure/) - Limited access online data warehousing and analysis platform for transportation researchers.

## Get Involved

USDOT ITS JPO is soliciting user feedback on the current folder hierarchy to determine what the best approach is and to help inform future directory hierarchies for other data types. To provide input on the hierarchy or the data, please [Open an Issue](https://github.com/usdot-its-jpo-data-portal/sandbox/issues). We welcome your feedback and ideas.