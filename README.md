# Accessing CV Pilots Data From a Public Amazon S3 Bucket

This document is meant to propose a data hierarchy to structure the processed data ingested from the CV Pilot programs and other streaming data sources. The system will provide multiple ways of viewing the data which will include an S3 bucket within AWS and various analytical or data views that will pull data from that S3 bucket. These analytical tools may include databases, noSQL, Athena, or other analytical tools to structure/reorganize and pull the data.

The S3 bucket provides an alternative that is similar to traversing a directory structure. The intention of the hierarchy is for it to provide a consistent structure within a pilot program, be easily understood by a human traversing the directories, be structured sufficiently so third parties can build software applications using the data, and to be flexible enough to capture different data types. 

The expectation is that different data types will lend themselves to different directory hierarchies. In addition, the different pilot sites may have compelling reasons to organize the data in different hierarchies for the same data type. The below hierarchy is intended for processed Basic Safety Messages (BSM) from the Wyoming CV Pilot site, where one message is captured per file. More details on BSM are available at http://standards.sae.org/j2735_201603/ and https://www.its.dot.gov/itspac/october2012/PDF/data_availability.pdf. We are soliciting user feedback on the current BSM hierarchy to determine what the best approach is and to help inform future directory hierarchies for other data types.

### Prerequisites

1) Have your own Amazon Web Services account.

	- Create one at aws.amazon.com
 
2) Obtain Access Keys:
 
	- On your amazon account, go to your profile (at the top right)
	 
	- My Security Credentials > Access Keys > Create New Access Key
	 
	- Keep Access Key ID and Secret Access Key ID
 
3) Have Amazon Web Services Command Line Interface (AWS CLI) installed on your computer.

	- Installation options can be found at aws.amazon.com/cli

	- To run AWS CLI on Windows, navigate to C:\Program Files\Amazon\ and run "aws
	 --version" to confirm that the program is installed.
 
4) Run the following command through AWS CLI:

aws configure
 
and enter the following:
 
* Access Key (from step 2)
* Secret Access Key (from step 2)
* Default region name (us-east-1)
* Default output format (ex: json)

## Getting Started

Now go to your command window. The title of the two s3 buckets are: 

 *	CV PEP (restricted access): usdot-its-cvpilot-eval-data
 *	RDE (public access): usdot-its-cvpilot-public-data

Run the following to check access:
```
aws s3 ls s3://*bucket name*/ --recursive --human-readable --summarize
```

####Directory structure within buckets:

The directory structure within the buckets will take the following form:

<Source_Name>/<Data_Type>/<Date_Time>/<Location>/<File_Name>

So for example, accessing Wyoming CV Pilots BSM data for a specific time and location will look like: 

wydot/BSM/2017-08-03T17:49:07+00:00/41.3N_-105.6E/wydot-filtered-bsm-1501782546127.json

Where in this example the actual file is titled 'wydot-filtered-bsm-1501782546127.json'.

#### Downloading from the S3 Bucket

To download from the S3 Bucket, enter the following command:

```
aws s3 sync {local_directory} s3://bucketname/
```
