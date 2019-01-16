import boto3
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
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


def process_spat(raw_rec):
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
    return out


def lambda_handler(event, context):
    '''
    '''
    start = time.time()
    out_recs = []
    for bucket, key in lambda_to_socrata_util.get_fps_from_event(event):
        raw_recs = lambda_to_socrata_util.process_s3_file(bucket, key)
        out_recs += [process_spat(i) for i in raw_recs]

    if len(out_recs) == 0:
        logger.info("No new data found. Exit script")
        return

    logger.info("Connecting to Socrata")
    client = Socrata("data.transportation.gov", SOCRATA_API_KEY, SOCRATA_USERNAME, SOCRATA_PASSWORD, timeout=400)

    logger.info("Transform record dtypes according to Socrata dataset")
    col_dtype_dict = lambda_to_socrata_util.get_col_dtype_dict(client, SOCRATA_DATASET_ID)
    out_recs = [lambda_to_socrata_util.mod_dtype(r, col_dtype_dict) for r in out_recs]

    logger.info("Uploading {} new records".format(len(out_recs)))
    uploadResponse = client.upsert(SOCRATA_DATASET_ID, out_recs)
    logger.info(uploadResponse)

    r = requests.get("https://data.transportation.gov/resource/{}.json?$select=count(*)".format(SOCRATA_DATASET_ID),
                    auth=HTTPBasicAuth(SOCRATA_USERNAME, SOCRATA_PASSWORD))
    r = r.json()
    count = int(r[0]['count'])
    if count > 3000000:
        toDelete = count - 3000000
        logger.info(toDelete)
        retrievedRows = client.get(SOCRATA_DATASET_ID, limit=toDelete, exclude_system_fields=False)
        deleteList = []
        for x in range(0,toDelete):
            tempDictionary = {}
            tempDictionary[':id'] = retrievedRows[x][':id']
            tempDictionary[':deleted'] = True
            deleteList.append(tempDictionary)
        logger.info("deleting now:")
        logger.info(client.upsert(SOCRATA_DATASET_ID, deleteList))
