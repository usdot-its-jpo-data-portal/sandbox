'''
This lambda function works with the Signal Phasing and Timing (SPaT) data from Tampa (THEA)
Connected Vehicle Pilot.

This lambda function is triggered by file creation in the ITS DataHub
Sandbox s3 bucket ("usdot-its-cvpilot-public-data" or "test-usdot-its-cvpilot-public-data").
When a new file is added to the Sandbox s3 bucket, this lambda function will read
the new JSON newline file, perform data transformation, and upsert the new data
records to the corresponding Socrata data set on data.transportation.gov.

Data transformation includes flattening of the data structure, which is
required for the data to work with the Socrata backend on data.transportation.gov.
Renaming of certain fields is done to achieve consistency across data sets. No
unit conversion will be done to the data, though occasionally, additional fields
will be added to enhance usage of the data set in Socrata (e.g. geolocation fields
for plotting). Any added fields will be listed in the description of each Socrata
data set.

A separate lambda function using the lambda handler in `lambda_function_cleanup.py`
will be used to keep the data set at a manageable size by removing oldest records
from the Socrata data set.

Requires:
- Uploading to AWS requires packaging the source code with the Python extensions
into a single zip file. This code requires the following Python libraries to be
packaged with the source code to work on AWS: requests, sodapy. The file
`lambda_to_socrata_util.py` that is in this repo should also be included.
- The user must also set the following Environment Variables in their lambda
function: SOCRATA_USERNAME, SOCRATA_PASSWORD, SOCRATA_API_KEY, SOCRATA_DATASET_ID.

'''
# import boto3
import s3fs
import dateutil.parser
from datetime import datetime, timedelta
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
import random
requests.packages.urllib3.disable_warnings()
from sodapy import Socrata
import time


import lambda_to_socrata_util


logger = logging.getLogger()
logger.setLevel(logging.INFO)


SOCRATA_USERNAME = os.environ['SOCRATA_USERNAME']
SOCRATA_PASSWORD = os.environ['SOCRATA_PASSWORD']
SOCRATA_API_KEY = os.environ['SOCRATA_API_KEY']
SOCRATA_DATASET_ID = os.environ['SOCRATA_DATASET_ID']
S3_BUCKET = os.environ['S3_BUCKET']
DATA_PROVIDER = os.environ['DATA_PROVIDER']
DATA_TYPE = os.environ['DATA_TYPE']


def process_spat(raw_rec):
    '''
    Reads each raw SPaT data record from Tampa CV Pilot and performs data transformation,
    including:
    1) Flatten the data structure
    2) Rename certain fields to achieve consistency across data sets
    3) Add additional fields to enhance usage of the dataset in Socrata
    (e.g. randomNum)

	Parameters:
		raw_rec: dictionary object of a single SPaT record

	Returns:
		transformed dictionary object of the SPaT record
    '''
    rename_fields = [
        ('metadata_dataType', 'dataType'),
        ('metadata_recordGeneratedAt', 'metadata_generatedAt'),
        ('metadata_recordGeneratedBy', 'metadata_generatedBy')
    ]

    int_fields = [
        'payload_data_SPAT_intersections_IntersectionState_id_id',
        'payload_data_SPAT_intersections_IntersectionState_revision',
        'payload_data_SPAT_intersections_IntersectionState_status',
        'payload_data_SPAT_intersections_IntersectionState_timeStamp',
        'payload_data_SPAT_timeStamp',
        'metadata_psid',
        'metadata_schemaVersion'
    ]
    json_string_fields = [
        'payload_data_SPAT_intersections_IntersectionState_states_MovementState'
    ]
    out = lambda_to_socrata_util.process_raw_recs(raw_rec, rename_fields=rename_fields, int_fields=int_fields,
                           json_string_fields=json_string_fields)

    metadata_generatedAt = dateutil.parser.parse(out['metadata_generatedAt'][:23])
    out['metadata_generatedAt'] = metadata_generatedAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    out['randomNum'] = random.random()
    out['metadata_generatedAt_timeOfDay'] = metadata_generatedAt.hour + metadata_generatedAt.minute/60 + metadata_generatedAt.second/3600
    return out


def lambda_handler(event, context):
    '''
    Method called by Amazon Web Services when the lambda trigger fires. This lambda
    is configured to be triggered by file creation in the ITS DataHub
    Sandbox s3 bucket ("usdot-its-cvpilot-public-data" or "test-usdot-its-cvpilot-public-data").
    When a new file is added to the Sandbox s3 bucket, this lambda function will read
    the new JSON newline file, perform data transformation, upsert the new data
    records to the corresponding Socrata data set on data.transportation.gov, and remove the
    oldest records from the Socrata dataset to keep the data set at a manageable size.

    Parameters:
    	event, context: Amazon Web Services required parameters. Describes triggering event.
    '''
    t0 = time.time()

    # Connect to s3 client
    s3 = s3fs.S3FileSystem()

    # Get all file paths from recent ingestion day
    ingest_day = datetime.now() - timedelta(days=2)
    day_dir_path = os.path.join(S3_BUCKET, DATA_PROVIDER, DATA_TYPE,
                                ingest_day.strftime('%Y'), ingest_day.strftime('%m'), ingest_day.strftime('%d'))
    logger.info("This is the day path used for updating the data: " + day_dir_path)
    if event.get('test') == True:
        day_dir_path = 'usdot-its-cvpilot-public-data/thea/SPAT/2019/05/01'
        logger.info("This is a test. Using test day path: {}".format(day_dir_path))

    hour_dirs = s3.ls(day_dir_path)

    # Condition for selecting only hours between 6-9 and 16-19 to present
    for i in list(hour_dirs):
        #print int(i.split('/')[6])
        #if int(i.split('/')[6]) not in [6,7,8,16,17,18]:
        if int(i.split('/')[6]) not in [8]:
            hour_dirs.remove(i)

    logger.info("Parsing data from the following hour directories: \n{}".format(",\n".join(hour_dirs)))

    fps = []
    for hour_dir in hour_dirs:
        fps += s3.ls(hour_dir)

    if len(fps) == 0:
        logger.info("No new files found. Exit script")
        return

    logger.info("{} file paths found in {}".format(len(fps), day_dir_path))

    if event.get('test') == True:
        fps = fps[:10]
        logger.info("This is a test. Only ingesting first 10 files")

    # Create a draft of the Socrata data set
    logger.info("Connecting to Socrata")
    client = Socrata("data.transportation.gov", SOCRATA_API_KEY, SOCRATA_USERNAME, SOCRATA_PASSWORD, timeout=400)

    col_dtype_dict = lambda_to_socrata_util.get_col_dtype_dict(client, SOCRATA_DATASET_ID)
    float_fields = ['randomNum', 'metadata_generatedAt_timeOfDay']

    # Create a draft of the Socrata data set
    draftDataset = requests.post('https://data.transportation.gov/api/views/{}/publication.json'.format(SOCRATA_DATASET_ID),
                              auth=(SOCRATA_USERNAME, SOCRATA_PASSWORD),
                              params={'method': 'copySchema'})
    logger.info(draftDataset.json())
    # Grab the ID of the working draft dataset
    workingID = draftDataset.json()['id']

    # Write the event files to the newly created dataset
    # Read data from the newly deposited file and
    # perform data transformation on the records
    num_fps_done = 0
    num_recs_processed = 0
    for fp in fps:
        num_fps_done += 1
        bucket = fp.split('/')[0]
        key = "/".join(fp.split('/')[1:])

        raw_recs = lambda_to_socrata_util.process_s3_file(bucket, key)
        # sample_recs = random.sample(raw_recs, int(len(raw_recs)*.1))
        out_recs = [process_spat(i) for i in raw_recs]

        # logger.info("Transform record dtypes according to Socrata dataset")
        out_recs = [lambda_to_socrata_util.mod_dtype(r, col_dtype_dict, float_fields) for r in out_recs]
        num_recs_processed += len(out_recs)

        # logger.info("Uploading {} new records".format(len(out_recs)))
        uploadResponse = client.upsert(workingID, out_recs)
        logger.info(uploadResponse)

        # check duration of function. If function has been running for more than 10 min,
        # end the for loop and publish data set
        t1 = time.time()
        if t1-t0 >= 810:
            # log number of remaining files that were not upserted
            logger.info("number of remaining files that were not upserted {}/{}".format((len(fps)-num_fps_done),len(fps)))
            break

    #Finally we replace the already published SPaT with the contents of the Virtual working SPaT
    logger.info("Publishing draft {} to dataset {}, expecting {} records".format(workingID, SOCRATA_DATASET_ID, num_recs_processed))
    publishResponse = requests.post('https://data.transportation.gov/api/views/{}/publication.json'.format(workingID),
                                    auth=(SOCRATA_USERNAME, SOCRATA_PASSWORD))
    logger.info(publishResponse.json())
