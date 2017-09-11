# Accessing CV Pilots Data From a Public Amazon S3 Bucket - Beta

This repository is meant to propose a data folder hierarchy to structure the processed data ingested from the Connected Vehicles (CV) Pilot programs and other streaming data sources. Currently this is a beta system using a folder hierarchy for processed Basic Safety Messages (BSM) from the Wyoming CV Pilot site.

We are soliciting user feedback on the current BSM folder hierarchy to determine what the best approach is and to help inform future directory hierarchies for other data types. The system will provide multiple ways of viewing the data which will include an S3 bucket within Amazon Web Services (AWS) and various analytical or data views that will pull data from that S3 bucket. These analytical tools may include databases, noSQL, Athena, or other analytical tools to structure/reorganize and pull the data.

The S3 bucket provides an alternative that is similar to traversing a directory structure. The intention of the hierarchy is for it to provide a consistent structure within a pilot program, be easily understood by a human traversing the directories, be structured sufficiently so third parties can build software applications using the data, and to be flexible enough to capture different data types. 

The expectation is that different data types will lend themselves to different directory hierarchies. In addition, the different pilot sites may have compelling reasons to organize the data in different hierarchies for the same data type. The below hierarchy is intended for processed BSMs from the Wyoming CV Pilot site, where one message is captured per file. More details on BSM are available at:

- [J2735 Standard](http://standards.sae.org/j2735_201603/)
- [Vehicle Based Data and Availability](https://www.its.dot.gov/itspac/october2012/PDF/data_availability.pdf) 

### Related ITS JPO Projects

- [Operational Data Environment (ODE)](https://github.com/usdot-jpo-ode/jpo-ode) - This ITS JPO Open Source tool is used to collect and process Connected Vehicle data in near real time, and route it to other data repositories, including the Amazon S3 bucket.  Processing performed by the ODE includes validation, integration, sanitization (removal of private data), and integration
- [Privacy Module](https://github.com/usdot-jpo-ode/jpo-cvdp) - This  ITS JPO Open source module is used to sanitize the data to ensure no personal information is shared with the public.  For more information on how this is done please review the documentation in the GitHub Repository.
- [Connected Vehicles Performance Evaluation Platform (CVPEP)](https://github.com/VolpeUSDOT/CV-PEP) - Limited access Platform for storing raw CV data for evaluation.
- [ITS JPO Data Site - Beta](https://www.its.dot.gov/data/) - Beta version of ITS JPO data site which allows users to search for various ITS data.

### Prerequisites

1) Have your own Amazon Web Services account.

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

## Getting Started

Now go to your command window. The title of the s3 bucket is: 

 *	RDE (public access): usdot-its-cvpilot-public-data

Run the following to check access:
```
aws s3 ls s3://{bucket name}/ --recursive --human-readable --summarize --profile {profile_name}
```

#### Directory structure within buckets:

The directory structure within the buckets will take the following form:

	{Source_Name}/{Data_Type}/{Date_Time}/{Location}/{File_Name}

So for example, accessing Wyoming CV Pilots BSM data for a specific time and location will look like: 


	wydot/BSM/20170815T234600645Z/41.3N_-105.6E/wydot-filtered-bsm-1501782546127.json


Where in this example the actual BSM file is titled 'wydot-filtered-bsm-1501782546127.json'.

#### Downloading from the S3 Bucket

To download all data from the S3 Bucket, enter the following command:

```
aws s3 cp s3://bucketname/ {local_directory} --recursive --profile public
```

To limit the data being dowloaded you can use AWS CLI's filtering which is detailed here: http://docs.aws.amazon.com/cli/latest/reference/s3/#use-of-exclude-and-include-filters.

## Data Types

### Wyoming CV Data

Near real-time feed of CV data coming in from the [Wyoming Connected Vehicle Pilot]( https://www.its.dot.gov/pilots/pilots_wydot.htm).

#### BSM Data Format

All files are in a JSON format and are broken into three core fields:

- metadata - Includes all additional metadata information added to the file to provide additional contex for the data
- payload - The [J2735 Standard](http://standards.sae.org/j2735_201603/) information that includes information like vehicle location, speed, and heading
- schemaVersion - Version number of the full file schema


Base Field Name | Field Name | Definition
 ---  |  ---  |  ---
metadata|generatedAt|Closest time to which the message was created, either signed or received by On Board Unit (OBU) in UTC format. This information is taken from the communication header.
metadata|logFileName|Name of the deposited file into the ODE
metadata|validSignature|Boolean of signed vs unsigned data based on the SCMS System
metadata|sanitized|Boolean value indicating whether the data has been sanitized by the[Privacy Module](https://github.com/usdot-jpo-ode/jpo-cvdp)
metadata|payloadType|Java class identifying the type of payload included with the message
metadata|serialId|Unique record identifier for the message
metadata|serialId/streamId|Stream that process the original log file
metadata|serialId/bundleSize|Size of the bundle within the processed file
metadata|serialId/bundleId|Bundle identifier
metadata|serialId/recordId|Record identier within the bundle
metadata|serialId/serialNumber|Combined identifier within open stream
metadata|receivedAt|Time the ODE received the data n UTC format
metadata|latency| Difference between generatedAt and receivedAt time in seconds
metadata|receivedAt|Time the ODE received the data in UTC format
metadata|latency| Difference in generatedAt and receivedAt time in seconds
metadata|schemaVersion|Version number of the metadata schema
payload| dataType| Type of J2735 message 
payload|data| This includes all fields from [J2735 Standard](http://standards.sae.org/j2735_201603/)
payload|schemaVersion|Version number of the payload schema
schemaVersion|N/A|Version number of the full file schema

#### Sample Data

- [Sample of Wyoming CV Data](/sample/wydot-filtered-bsm-1502840971677.json)



#### Doing simple data analysis on the Wyoming Connected Vehicles (CV) Data

A basic tutorial Covering acceessing the data in a Python Jupyter Notebook:
- [Introduction to WY CV data through ITS JPO Sandbox](notebooks/Introduction%20to%20WY%20CV%20data%20through%20ITS%20JPO%20Sandbox.ipynb) 



