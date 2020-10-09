# Accessing Data in ITS Sandbox

**Table of Contents**

* [Background](#backgound)
	* [Related ITS JPO Projects](#related-its-jpo-projects)
* [Getting Started](#getting-started)
	* [AWS CLI](#aws-cli)
		* [Prerequisites for using AWS CLI](#prerequisites-for-using-aws-cli)
		* [Accessing Files through AWS CLI](#accessing-files-through-aws-cli)
		* [Directory Structure](#directory-structure)
		* [Downloading from S3](#downloading-from-s3)
	* [Sandbox Exporter](#sandbox-exporter)
		* [Prerequisites for using Sandbox Exporter](#prerequisites-for-using-sandbox-exporter)
		* [Exporting Data to CSV with Sandbox Exporter](#exporting-data-to-csv-with-sandbox-exporter)
 * [Data Types](#data-types)
 	* [CV Pilot Data](#cv-pilot-data)
 	  * [Wyoming CV Data](#wyoming)
	  * [Tampa CV Data](#tampa)
	* [Work Zone Data Exchange Feed Data](#wzdx-feed-data)
* [Get Involved](#get-involved)

## Background
This repository contains information on accessing complete datasets from the United States Department of Transportation (USDOT) Joint Program Office (JPO) data program's ITS Sandbox. It is meant to propose a data folder hierarchy to structure the processed data ingested from the Connected Vehicles (CV) Pilot programs, Work Zone Data Exchange (WZDx) programs, and other streaming data sources, as well as direct users to related tools and resources.

Currently this repository contains beta folder hierarchy systems for:
- Connected Vehicle (CV) Pilot:
	- Wyoming CV Pilot site: processed Basic Safety Messages (BSM), Traveler Information Messages (TIM)
	- Tampa CV Pilot site: BSM, TIM, and Signal Phasing and Timing (SPaT) data
- Work Zone Data Exchange (WZDx) Feed Archive:
	- Maricopa County WZDx Feed

USDOT JPO is soliciting user feedback on the current folder hierarchy to determine what the best approach is and to help inform future directory hierarchies for other data types. To provide input on the hierarchy or the data please [Open an Issue](https://github.com/usdot-its-jpo-data-portal/sandbox/issues).

The AWS S3 bucket provides an alternative that is [similar to traversing a directory structure](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html). The intention of the hierarchy is to:

- Provide a consistent structure within a pilot program
- Be easily understood by a human traversing the directories
- Be structured sufficiently so third parties can build software applications using the data
- Be flexible enough to capture different data types.

The expectation is that different data types will lend themselves to different directory hierarchies. In addition, the pilot sites may have compelling reasons to organize the data in different hierarchies for the same data type. The below hierarchy is intended for processed BSMs, TIMs, and SPaTs from the Wyoming and Tampa CV Pilot sites.

Additional information about CV data is available at:

- [ITS JPO Connected Vehicles (CV) Pilot Deployment Program](https://www.its.dot.gov/pilots/cv_pilot_plan.htm)-  The pilot deployments are expected to integrate connected vehicle research concepts into practical and effective elements, enhancing existing operational capabilities.
- [J2735 Standard](http://standards.sae.org/j2735_201603/) -  Standard for CV data
- [General CV information: Vehicle Based Data and Availability](https://www.its.dot.gov/itspac/october2012/PDF/data_availability.pdf) - General introduction slides on CV data

Additional information about the WZDx specifications is available at:

- [WZDx Specification GitHub repository](https://github.com/usdot-jpo-ode/jpo-wzdx)

### Related ITS JPO Projects

- [ITS DataHub](https://www.its.dot.gov/data/) - ITS JPO data site which allows users to search for various ITS data.
- [Operational Data Environment (ODE)](https://github.com/usdot-jpo-ode/jpo-ode) - This ITS JPO Open Source tool is used to collect and process Connected Vehicle data in near real time, and route it to other data repositories, including the Amazon S3 bucket.  
- [Privacy Module](https://github.com/usdot-jpo-ode/jpo-cvdp) - This ITS JPO Open source module is used to sanitize the data to ensure no personal information is shared with the public.  
- [Secure Data Commons(SDC)](https://github.com/usdot-jpo-sdc) - Limited access online data warehousing and analysis platform for transportation researchers.

## Getting Started

There are three ways to access the full data sets on Amazon s3. The first way is through the [Web Interface](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html). This allows the user to browse through the folder structure and click and download individual batched data files. Alternatively, the data can be downloaded programmatically using the [Amazon Command Line Interface (CLI)](#aws-cli) or our [Sandbox Export script](#sandbox-exporter) by following the directions below.

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

Now go to your command window. The title of the s3 bucket is:

 *	RDE (public access): usdot-its-cvpilot-public-data

Run the following to check access:
```
aws s3 ls s3://{bucket name}/ --recursive --human-readable --summarize --profile {profile_name}
```

For Example:
```
aws s3 ls s3://usdot-its-cvpilot-public-data/ --recursive --human-readable --summarize --profile default
```

#### Directory Structure

The directory structure within the buckets will take the following form, with the year, month, day, hour based on when the data point was generated.

	`{Source_Name}/{Data_Type}/{Year}/{Month}/{Day}/{Hour}`

So for example, accessing Wyoming CV Pilots BSM data for a specific time will look like:

	`wydot/BSM/2017/08/15/23/wydot-filtered-bsm-1501782546127.json`

Where in this example the actual BSM file is titled 'wydot-filtered-bsm-1501782546127.json'. For Wyoming CV Pilot data, data prior to January 18, 2018 is one message per file. From that date onwards, files will contain multiple messages.

#### Downloading from S3

To download all data from the S3 Bucket, enter the following command:

```
aws s3 cp s3://{bucketname}/{local_directory} --recursive
```

For example, to download all BSM data from 2017:
```
aws s3 cp s3://usdot-its-cvpilot-public-data/wydot/BSM/2017/ --recursive
```

To limit the data being dowloaded you can use AWS CLI's filtering which is detailed here: http://docs.aws.amazon.com/cli/latest/reference/s3/#use-of-exclude-and-include-filters.

### Sandbox Exporter

You can also download data generated between a specified date range into larger merged CSV or JSON file(s) by using our Sandbox Exporter resource. Please refer to the README at our [cv_pilot_ingest](https://github.com/usdot-its-jpo-data-portal/cv_pilot_ingest) GitHub repository. The Sandbox Exporter currently only works for CV Pilot data and not for the WZDx data.

## Data Types

### CV Pilot Data
CV Pilot data are located in the `usdot-its-cvpilot-public-data` s3 bucket.
Test CV Pilot data are located in the `test-usdot-its-cvpilot-public-data` s3 bucket.

**Caution:** Other than organizing data by their generated-at timestamps, data in the CV Pilot (CVP) Sandbox are provided as they were received from data providers with no additions or modifications. Data may be available in the CVP Sandbox on the day they were generated or with a couple of days of lag from the date of generation. Please consult our [log of known data pipeline downtime and caveats](https://github.com/usdot-its-jpo-data-portal/sandbox/wiki/ITS-CV-Pilot-Data-Sandbox-Known-Data-Gaps-and-Caveats) prior to using the data.

#### Wyoming

Wyoming (WYDOT) currently provides sanitized BSM and TIM data to the public through ITS DataHub. Data from WYDOT are generated 7 days a week.

- The full sanitized WYDOT BSM and TIM data set can be found in the [ITS DataHub sandbox s3 bucket](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html) under `wydot/` folder prefix
- Sample WYDOT CV data sets on data.transportation.gov can be found [here](https://data.transportation.gov/browse?tags=wyoming%20connected%20vehicle%20%28cv%29%20pilot)
- Wyoming CV BSM/TIM schema descriptions can be found in the [ODE Output Schema Reference](https://github.com/usdot-jpo-ode/jpo-ode/blob/master/docs/ODE_Output_Schema_Reference.docx) document

#### Tampa

Tampa (THEA) currently provides sanitized BSM, TIM, and SPaT data to the public through ITS DataHub. For THEA, only data generated on weekdays are publicly accessible.

- The full sanitized THEA BSM, TIM, and SPaT data set can be found in the [ITS DataHub sandbox s3 bucket](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html) under `thea/` folder prefix
- Sample THEA CV data sets on data.transportation.gov can be found [here](https://data.transportation.gov/browse?tags=tampa+connected+vehicle+pilot+deployment+%28tampa+cv+pilot%29&utf8=%E2%9C%93)

#### Doing simple data analysis on the Wyoming Connected Vehicles (CV) Data		

 -A basic tutorial covering accessing the data in a Python Jupyter Notebook
 (note analysis of the data can be done by almost any programming langauge just Python was selected for this example):

 - [Introduction to WY CV data through ITS JPO Sandbox](example/accessing_wydot.ipynb)

### WZDx Feed Data

WZDx data are located in the `usdot-its-workzone-public-data` s3 bucket.
Test WZDx data are located in the `test-usdot-its-workzone-public-data` s3 bucket.

MCDOT WZDx feed is currently the only feed being ingested and archived into the [ITS Work Zone Sandbox](http://usdot-its-workzone-public-data.s3.amazonaws.com/index.html), using code in the [wzdx_sandbox](https://github.com/usdot-its-jpo-data-portal/wzdx_sandbox) GitHub repository. Users can check whether or not a WZDx feed is being ingested into the sandbox by checking the [WZDx Feed Registry](https://datahub.transportation.gov/d/69qe-yiui), and new WZDx feeds will be added to the feed registry as they become available.

## Get Involved
------------

We welcome your feedback and ideas. Here's how to reach us:
- [Open an Issue](https://github.com/usdot-its-jpo-data-portal/sandbox/issues)
