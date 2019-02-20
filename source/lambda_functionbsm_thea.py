'''
This lambda function works with the Basic Safety Message (BSM) data from Tampa (THEA)
Connected Vehicle Pilot.

This lambda function is triggered by file creation in the ITS DataHub
Sandbox s3 bucket ("usdot-its-cvpilot-public-data" or "test-usdot-its-cvpilot-public-data").
When a new file is added to the Sandbox s3 bucket, this lambda function will read
the new JSON newline file, perform data transformation, upsert the new data
records to the corresponding Socrata data set on data.transportation.gov, and remove the
oldest records from the Socrata dataset to keep the data set at a manageable size.

Data transformation includes flattening of the data structure, which is
required for the data to work with the Socrata backend on data.transportation.gov.
Renaming of certain fields is done to achieve consistency across data sets. No
unit conversion will be done to the data, though occasionally, additional fields
will be added to enhance usage of the dataset in Socrata (e.g. geolocation fields
for plotting). Any added fields will be listed in the description of each Socrata
data set.

The lambda function will delete 10,000 of the oldest records in the data set when
the number of records exceeds 3 million. This allows the data set to hold a sample
of the most recent ~3 million records and allows the data set to be accessible
on data.transportation.gov with minimal lags.

Requires:
- Uploading to AWS requires packaging the source code with the Python extensions
into a single zip file. This code requires the following Python libraries to be
packaged with the source code to work on AWS: requests, sodapy. The file
`lambda_to_socrata_util.py` that is in this repo should also be included.
- The user must also set the following Environment Variables in their lambda
function: SOCRATA_USERNAME, SOCRATA_PASSWORD, SOCRATA_API_KEY, SOCRATA_DATASET_ID.

'''
import boto3
import dateutil.parser
import json
import logging
import os
import random
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
    '''
    Reads each raw BSM data record from Tampa CV Pilot and performs data transformation,
    including:
    1) Flatten the data structure
    2) Rename certain fields to achieve consistency across data sets
    3) Add additional fields to enhance usage of the dataset in Socrata
    (e.g. randomNum, coreData_position)

	Parameters:
		raw_rec: dictionary object of a single BSM record

	Returns:
		transformed dictionary object of the BSM record
    '''
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
        coreData_position_long = float(out['coreData_position_long'])/10e6
        coreData_position_lat = float(out['coreData_position_lat'])/10e6
        out['coreData_position'] = "POINT ({} {})".format(coreData_position_long, coreData_position_lat)

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

    out['metadata_generatedAt'] = dateutil.parser.parse(out['metadata_generatedAt'][:23]).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    out['randomNum'] = random.random()
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
    # Read data from the newly deposited file and
    # perform data transformation on the records
    out_recs = []
    for bucket, key in lambda_to_socrata_util.get_fps_from_event(event):
        raw_recs = lambda_to_socrata_util.process_s3_file(bucket, key)
        out_recs += [process_bsm(i) for i in raw_recs]

    if len(out_recs) == 0:
        logger.info("No new data found. Exit script")
        return

    # Upsert the new records to the corresponding Socrata data set
    logger.info("Connecting to Socrata")
    client = Socrata("data.transportation.gov", SOCRATA_API_KEY, SOCRATA_USERNAME, SOCRATA_PASSWORD, timeout=400)

    logger.info("Transform record dtypes according to Socrata dataset")
    col_dtype_dict = lambda_to_socrata_util.get_col_dtype_dict(client, SOCRATA_DATASET_ID)
    float_fields = ['randomNum']
    out_recs = [lambda_to_socrata_util.mod_dtype(r, col_dtype_dict, float_fields) for r in out_recs]

    logger.info("Uploading {} new records".format(len(out_recs)))
    uploadResponse = client.upsert(SOCRATA_DATASET_ID, out_recs)
    logger.info(uploadResponse)

    # If the corresponding Socrata data set has more than 3 million records,
    # remove the oldest 10k records to keep the data set at a manageable size
    r = requests.get("https://data.transportation.gov/resource/{}.json?$select=count(*)".format(SOCRATA_DATASET_ID),
                    auth=HTTPBasicAuth(SOCRATA_USERNAME, SOCRATA_PASSWORD))
    r = r.json()
    count = int(r[0]['count'])
    if count > 3000000:
        logger.info('{} rows in dataset - removing oldest 10k rows'.format(count))
        N = 10000
        retrievedRows = client.get(SOCRATA_DATASET_ID, limit=N, exclude_system_fields=False)
        deleteList = [{':id': row[':id'], ':deleted': True} for row in retrievedRows]
        try:
            result = client.upsert(SOCRATA_DATASET_ID, deleteList)
        except:
            time.sleep(2)
            result = client.upsert(SOCRATA_DATASET_ID, deleteList)
        logger.info(result)
