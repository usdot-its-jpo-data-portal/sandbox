"""
Move gz json file from ingest s3 bucket to ITS DataHub sandbox s3.

"""

from __future__ import print_function

import logging
import boto3
from datetime import datetime
from gzip import GzipFile
from io import TextIOWrapper
import json
import os
import requests
import traceback
import uuid


logger = logging.getLogger()
logger.setLevel(logging.INFO)  # necessary to make sure aws is logging

CHANNEL = os.environ['SLACK_CHANNEL']
USERNAME = os.environ['SLACK_USERNAME']
WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']

SOURCE_PREFIX = os.environ['SOURCE_S3_PREFIX']
TARGET_BUCKET = os.environ['TARGET_S3_BUCKET']
TARGET_PREFIX = os.environ['TARGET_S3_PREFIX']

STREAM_VERSION = 0

def send_to_slack(msg, channel=CHANNEL, username=USERNAME, webhook_url=WEBHOOK_URL):
#     slack_url = 'https://slack.com/api/chat.postMessage'
    PAYLOAD = {
        "channel": channel,
        "username": username,
        "attachments": [
            {
                "text": msg
            }
        ]
    }
    r = requests.post(webhook_url, data=json.dumps(PAYLOAD))
    return r

def get_fps_from_event(event):
    bucket_key_tuples = [(e['s3']['bucket']['name'], e['s3']['object']['key']) for e in event['Records']]
    bucket_key_dict = {os.path.join(bucket, key): (bucket, key) for bucket, key in bucket_key_tuples}
    bucket_key_tuples_deduped = list(bucket_key_dict.values())
    return bucket_key_tuples_deduped

def s3_gzip_data_reader(bucket, key):
    s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    gzipped = GzipFile(None, 'rb', fileobj=obj['Body'])
    data = TextIOWrapper(gzipped)
    return data

def s3_gzip_data_generator(bucket, key):
    data = s3_gzip_data_reader(bucket, key)
    for line in data:
        yield json.loads(line)

def move_new_file(source_bucket, source_key):
    s3_client = boto3.client('s3')

    # read triggering gz file
    source_path = os.path.join(source_bucket, source_key)
    logging.info('Triggered by file: {}'.format(source_path))

    # get first timestamp
    has_data = False
    for rec in s3_gzip_data_generator(source_bucket, source_key):
        has_data = True
        recordGeneratedAt = rec['metadata']['recordGeneratedAt']
        recordGeneratedAt_dt = datetime.strptime(recordGeneratedAt[:19], '%Y-%m-%d %H:%M:%S')
        break

    if has_data:
        # generate outpath
        target_prefix_template = '{pilot_name}/{message_type}/{year}/{month}/{day}/{hour}/'
        target_filename_template = '{filename_prefix}-{message_type_lower}-public-{stream_version}-{ymdhms}-{uuid}'

        path_params = {
            'pilot_name': TARGET_PREFIX.strip('/').strip().lower(),
            'message_type': source_key.strip(SOURCE_PREFIX).split('/')[0],
            'year': recordGeneratedAt_dt.strftime('%Y'),
            'month':recordGeneratedAt_dt.strftime('%m'),
            'day': recordGeneratedAt_dt.strftime('%d'),
            'hour': recordGeneratedAt_dt.strftime('%H'),
            'filename_prefix': TARGET_BUCKET.replace('-public-data', ''),
            'stream_version': STREAM_VERSION,
            'ymdhms': recordGeneratedAt_dt.strftime('%Y-%m-%d-%H-%M-%S'),
            'uuid': uuid.uuid4()
        }
        path_params['message_type_lower'] = path_params['message_type'].lower()

        target_prefix = target_prefix_template.format(**path_params)
        target_file_name = target_filename_template.format(**path_params)
        target_key = os.path.join(target_prefix, target_file_name)
        target_path = os.path.join(TARGET_BUCKET, target_key)

        # copy data
        logging.info('Copying file: {} -> {}'.format(source_path, target_path))
        source_data = s3_gzip_data_reader(source_bucket, source_key)
        s3_client.put_object(Bucket=TARGET_BUCKET, Key=target_key, Body=source_data.read())
        logging.info('File copied')
    else:
        logging.info('File is empty: {}'.format(source_path))

    # delete file
    logging.info('Delete file: {}'.format(source_path))
    s3_client.delete_object(Bucket=source_bucket, Key=source_key)
    return

def lambda_handler(event, context):
    """AWS Lambda handler. processes manual uploads to manual ingest bucket"""

    for bucket, key in get_fps_from_event(event):
        try:
            move_new_file(bucket, key)
        except Exception as e:
            send_to_slack(traceback.format_exc())
            logging.error("Received error: {}".format(e), exc_info=True)
            logging.error('Exception on event record: '.format(event_rec))
            raise e
    logging.info('Processed events')
