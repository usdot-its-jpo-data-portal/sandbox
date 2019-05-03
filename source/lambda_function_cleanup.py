'''
This lambda function remove old records from Socrata data sets to keep it at
a certain size.

This lambda function is scheduled to run at regular intervals to check the current
size of specified Socrata data sets. If the Socrata data set has more than a specified number
of records, it will remove chunks of oldest rows until the data set is at a
specified size.

This allows the data set to hold a sample of the most recent x number records
and allows the data set to be accessible on data.transportation.gov with minimal lags.

Requires:
- Uploading to AWS requires packaging the source code with the Python extensions
into a single zip file. This code requires the following Python libraries to be
packaged with the source code to work on AWS: requests, sodapy.
- The user must also set the following Environment Variables in their lambda
function: SOCRATA_USERNAME, SOCRATA_PASSWORD, SOCRATA_API_KEY, SOCRATA_DATASET_IDS,
SOCRATA_DOMAIN, DATASET_LIMIT
- SOCRATA_DATASET_IDS should be a comma delimited string of the socrata data set ids

'''
import boto3
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
import random
requests.packages.urllib3.disable_warnings()
from sodapy import Socrata
import time


logger = logging.getLogger()
logger.setLevel(logging.INFO)


SOCRATA_USERNAME = os.environ['SOCRATA_USERNAME']
SOCRATA_PASSWORD = os.environ['SOCRATA_PASSWORD']
SOCRATA_API_KEY = os.environ['SOCRATA_API_KEY']
SOCRATA_DATASET_IDS = os.environ['SOCRATA_DATASET_IDS']
SOCRATA_DOMAIN = os.environ['SOCRATA_DOMAIN'] or "data.transportation.gov"
DATASET_LIMIT = os.environ['DATASET_LIMIT'] or 3000000

DATASET_LIMIT = int(DATASET_LIMIT)
SOCRATA_DATASET_IDS = SOCRATA_DATASET_IDS.split(',')
SOCRATA_DATASET_IDS = [i.strip() for i in SOCRATA_DATASET_IDS]
random.shuffle(SOCRATA_DATASET_IDS)


def lambda_handler(event, context):
    '''
    Method called by Amazon Web Services when the lambda trigger fires.
    This lambda is configured to be triggered at regular intervals.
    It will remove old records from Socrata data sets to keep it at
    a certain size.

    Parameters:
    	event, context: Amazon Web Services required parameters. Describes triggering event.
    '''
    logger.info("Connecting to Socrata")
    client = Socrata(SOCRATA_DOMAIN, SOCRATA_API_KEY, SOCRATA_USERNAME, SOCRATA_PASSWORD, timeout=400)

    # check number of records in each socrata data set
    # keep track of data sets that have more than x records
    id_toDelete_dict = {}
    for datasetId in SOCRATA_DATASET_IDS:
        r = requests.get("https://{}/resource/{}.json?$select=count(*)".format(SOCRATA_DOMAIN, datasetId),
                        auth=HTTPBasicAuth(SOCRATA_USERNAME, SOCRATA_PASSWORD))
        r = r.json()
        count = int(r[0]['count'])
        if count > DATASET_LIMIT:
            toDelete = count - DATASET_LIMIT
            id_toDelete_dict[datasetId] = toDelete
            logger.info('data set {} has {} rows - removing oldest {} rows'.format(datasetId, count, toDelete))
        else:
            logger.info('data set {} has {} rows - no action needed'.format(datasetId, count))
        time.sleep(5)

    # loop through data set to remove excess records
    # remove the oldest records to keep the data set at a manageable size
    # wait at end of each loop if hitting error
    wait = False
    while bool(id_toDelete_dict):
        for datasetId, toDelete in id_toDelete_dict.items():
            try:
                # remove at most 10000 records at a time to avoid timeouts
                N = min(toDelete, 10000)
                retrievedRows = client.get(datasetId, limit=N, exclude_system_fields=False,
                                           select=':id,metadata_generatedAt', order='metadata_generatedAt')
                deleteList = [{':id': row[':id'], ':deleted': True} for row in retrievedRows]
                result = client.upsert(datasetId, deleteList)
                logger.info(id_toDelete_dict)
                toDelete = toDelete - N
                id_toDelete_dict[datasetId] = toDelete
                if not toDelete > 0:
                    del id_toDelete_dict[datasetId]
                if len(id_toDelete_dict) == 1:
                    time.sleep(1)
            except:
                logger.info('Error while deleting {} records in {}. Skipping for now'.format(N, datasetId))
                wait = True
        if wait:
            logger.info('Slow down a bit. Wait 2 seconds.')
            time.sleep(2)
            wait = False
