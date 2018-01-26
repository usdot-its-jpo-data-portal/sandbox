# Accessing CV Pilots Data From a Public Amazon S3 Bucket


**Table of Contents**

* [Background](#backgound)
	* [Related ITS JPO Projects](#related-its-jpo-projects)
* [Getting Started](#getting-started)
	* [Prerequisites for using AWS CLI](#prerequisites-for-using-aws-cli)
	* [Accessing Files through AWS CLI](#accessing-files-through-aws-cli)
	* [Directory Structure](#directory-structure)
	* [Downloading from S3](#downloading-from-s3)
 * [Data Types](#data-types)
 	* [Wyoming CV Data](#wyoming-cv-data)
* [Get Involved](#get-involved)

## Background
This repository contains information on accessing complete data sets from the United States Department of Transportation (USDOT) Joint Program Office (JPO) data program. It is meant to propose a data folder hierarchy to structure the processed data ingested from the Connected Vehicles (CV) Pilot programs and other streaming data sources. Currently this is a beta system using a folder hierarchy for processed Basic Safety Messages (BSM) and Traveler Information Messages (TIM) from the Wyoming CV Pilot site.

USDOT JPO is soliciting user feedback on the current folder hierarchy to determine what the best approach is and to help inform future directory hierarchies for other data types. To provide input on the hierarchy or the data please [Open an Issue](https://github.com/usdot-its-jpo-data-portal/sandbox/issues). 

The AWS S3 bucket provides an alternative that is [similar to traversing a directory structure](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html). The intention of the hierarchy is to: 

- Provide a consistent structure within a pilot program
- Be easily understood by a human traversing the directories
- Be structured sufficiently so third parties can build software applications using the data
- Be flexible enough to capture different data types. 

The expectation is that different data types will lend themselves to different directory hierarchies. In addition, the pilot sites may have compelling reasons to organize the data in different hierarchies for the same data type. The below hierarchy is intended for processed BSMs from the Wyoming CV Pilot site. 

Additional information about CV data is available at:

- [ITS JPO Connected Vehicles (CV) Pilot Deployment Program](https://www.its.dot.gov/pilots/cv_pilot_plan.htm)-  The pilot deployments are expected to integrate connected vehicle research concepts into practical and effective elements, enhancing existing operational capabilities.
- [J2735 Standard](http://standards.sae.org/j2735_201603/) -  Standard for CV data
- [General CV information: Vehicle Based Data and Availability](https://www.its.dot.gov/itspac/october2012/PDF/data_availability.pdf) - General introduction slides on CV data
- [Sample of the WYDOT BSM data](https://data.transportation.gov/Automobiles/Wyoming-CV-Pilot-Basic-Safety-Message-One-Day-Samp/9k4m-a3jc) - Sample of WYDOT BSM data

### Related ITS JPO Projects

- [ITS JPO Data Site ](https://www.its.dot.gov/data/) -  ITS JPO data site which allows users to search for various ITS data.
- [Operational Data Environment (ODE)](https://github.com/usdot-jpo-ode/jpo-ode) - This ITS JPO Open Source tool is used to collect and process Connected Vehicle data in near real time, and route it to other data repositories, including the Amazon S3 bucket.  
- [Privacy Module](https://github.com/usdot-jpo-ode/jpo-cvdp) - This  ITS JPO Open source module is used to sanitize the data to ensure no personal information is shared with the public.  
- [Connected Vehicles Performance Evaluation Platform (CVPEP)](https://github.com/VolpeUSDOT/CV-PEP) - Limited access Platform for storing raw CV data for evaluation.



## Getting Started

There are two ways to access the full data sets on Amazon s3. The first way is through the [Web Interface](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html). This allows the user to browse through the folder structure and click and download individual BSMs. Alternatively, the data can be downloaded programmatically using the Amazon Command Line Interface (CLI) by following the directions below.

### Prerequisites for using AWS CLI

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

### Accessing files through AWS CLI

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

### Directory Structure

The directory structure within the buckets will take the following form:

	{Source_Name}/{Data_Type}/{Year}/{Month}/{Day}/{Hour}

So for example, accessing Wyoming CV Pilots BSM data for a specific time will look like: 


	wydot/BSM/2017/08/15/23/wydot-filtered-bsm-1501782546127.json
 
Where in this example the actual BSM file is titled 'wydot-filtered-bsm-1501782546127.json'. Data prior to January 18, 2018 is one message per file, from that date onwards files will contain multiple messages. 

### Downloading from S3

To download all data from the S3 Bucket, enter the following command:

```
aws s3 cp s3://{bucketname}/{local_directory} --recursive
```

For example, to download all BSM data from 2017:
```
aws s3 cp s3://usdot-its-cvpilot-public-data/wydot/BSM/2017/ --recursive
```

To limit the data being dowloaded you can use AWS CLI's filtering which is detailed here: http://docs.aws.amazon.com/cli/latest/reference/s3/#use-of-exclude-and-include-filters.

## Data Types



### Wyoming CV Data

- [Details on Wyoming CV DATA BSMs and TIMs messages and samples](https://github.com/usdot-jpo-ode/jpo-ode/blob/develop/docs/metadata_standards.md)
- [Full data set in AWS](http://usdot-its-cvpilot-public-data.s3.amazonaws.com/index.html)

#### WYDOT BSM

- [Single file Sample](https://github.com/usdot-its-jpo-data-portal/sandbox/blob/master/sample/wydot-filtered-bsm-1512496037271.json)
- [Sample Data](https://data.transportation.gov/Automobiles/Wyoming-CV-Pilot-Basic-Safety-Message-One-Day-Samp/9k4m-a3jc)
#### WYDOT TIM

- [Single file Sample](https://github.com/usdot-its-jpo-data-portal/sandbox/blob/master/sample/wydot-filtered-tim-1512415831724.json)

#### Doing simple data analysis on the Wyoming Connected Vehicles (CV) Data		
  		  
 -A basic tutorial covering accessing the data in a Python Jupyter Notebook 
 (note analysis of the data can be done by almost any programming langauge just Python was selected for this example):

 - [Introduction to WY CV data through ITS JPO Sandbox](example/accessing_wydot.ipynb)

## Get Involved
------------

We welcome your feedback and ideas. Here's how to reach us:

- [Open an Issue](https://github.com/usdot-its-jpo-data-portal/sandbox/issues)




