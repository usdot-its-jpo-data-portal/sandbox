import boto3
import json
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


def process_bsm(raw_rec):

    rename_prefix_fields = [
        ('payload_data_coreData_', 'coreData_'),
        ('coreData_accelSet_', 'coreData_accelset_')
    ]
    rename_fields = [
        ('metadata_dataType', 'dataType'),
        ('metadata_recordGeneratedAt', 'metadata_generatedAt'),
        ('metadata_recordGeneratedBy', 'metadata_generatedBy'),
        ('coreData_lat', 'coreData_position_lat'),
        ('coreData_long', 'coreData_position_long'),
        ('coreData_elev', 'coreData_elevation'),
        ('coreData_accelset_yaw', 'coreData_accelset_accelYaw')
    ]
    int_fields = [
        'metadata_psid',
        'metadata_schemaVersion']
    out = lambda_to_socrata_util.process_raw_recs(raw_rec,
                           rename_prefix_fields=rename_prefix_fields,
                           rename_fields=rename_fields,
                           int_fields=int_fields)

    def set_part2_element(out, part2_val):
        part2_val_out = lambda_to_socrata_util.process_raw_recs(part2_val,
         rename_prefix_fields=[('classDetails_', 'part2_suve_cd_'),
                               ('vehicleData_', 'part2_suve_vd_'),
                               ('vehicleAlerts_events_', 'part2_spve_vehalert_event_'),
                               ('vehicleAlerts_', 'part2_spve_vehalert_'),
                               ('trailers_', 'part2_spve_tr_'),
                               ('description_', 'part2_spve_event_'),
                               ('events_', 'part2_vse_events'),
                               ('pathHistory_', 'part2_vse_ph_'),
                               ('pathPrediction_', 'part2_vse_pp_'),
                               ('lights_', 'part2_vse_lights'),
                               ('coreData_accelSet', 'coreData_accelset_')
                              ],
         rename_fields=[('classification', 'part2_suve_classification'),
                        ('part2_spve_event_description', 'part2_spve_event_desc'),
                        ('part2_spve_tr_connection', 'part2_spve_tr_conn'),
                        ('part2_spve_tr_sspRights', 'part2_spve_tr_ssprights'),
                        ('events', 'part2_vse_events'),
                        ('part2_vse_pp_radiusOfCurve', 'part2_vse_pp_radiusofcurve'),
                        ('part2_vse_ph_crumbData_PathHistoryPoint', 'part2_vse_ph_crumbdata'),
                        ('part2_suve_cd_hpmsType', 'part2_suve_cd_hpmstype')
                       ],
         json_string_fields=['part2_vse_ph_crumbdata'],
        )
        out.update(part2_val_out)
        return out

    if 'payload_data_partII_SEQUENCE' in out:
        for elem in out['payload_data_partII_SEQUENCE']:
            for part2_type, part2_val in elem['partII-Value'].items():
                out = set_part2_element(out, part2_val)
        del out['payload_data_partII_SEQUENCE']

    if 'coreData_position_long' in out:
        out['coreData_position'] = "POINT ({} {})".format(out['coreData_position_long'], out['coreData_position_lat'])

    if 'coreData_size_width' in out:
        out['coreData_size'] = json.dumps({'width': int(out['coreData_size_width']),
                                           'length': int(out['coreData_size_length'])})
        del out['coreData_size_width']
        del out['coreData_size_length']

    if 'coreData_brakes_wheelBrakes' in out:
        out['coreData_brakes_wheelBrakes_unavailable'] = out['coreData_brakes_wheelBrakes'][0]
        out['coreData_brakes_wheelBrakes_leftFront'] = out['coreData_brakes_wheelBrakes'][1]
        out['coreData_brakes_wheelBrakes_leftRear'] = out['coreData_brakes_wheelBrakes'][2]
        out['coreData_brakes_wheelBrakes_rightFront'] = out['coreData_brakes_wheelBrakes'][3]
        out['coreData_brakes_wheelBrakes_rightRear'] = out['coreData_brakes_wheelBrakes'][4]
        del out['coreData_brakes_wheelBrakes']

    return out


def lambda_handler(event, context):
    '''
    '''
    start = time.time()
    out_recs = []
    for bucket, key in lambda_to_socrata_util.get_fps_from_event(event):
        raw_recs = lambda_to_socrata_util.process_s3_file(bucket, key)
        out_recs += [process_bsm(i) for i in raw_recs]

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
