'''
This file contains many helper functions for the lambda functions that
transform and load data from ITS DataHub Sandbox S3 bucket to Socrata data sets
on data.transportation.gov.

This file should be included in the zipped package for Tampa (THEA) Connected
Vehicle Pilot lambda functions.

'''
import boto3
import copy
import itertools
import json
import os


def get_fps_from_event(event):
    '''
    Retrieves file path associated with an S3 file creation event.

	Parameters:
		event: S3 file creation event sent by AWS lambda trigger

	Returns:
		list of (bucket, key) tuples of the S3 files that were created as
        part of the S3 file creation event
    '''
    bucket_key_tuples = [(e['s3']['bucket']['name'], e['s3']['object']['key']) for e in event['Records']]
    bucket_key_dict = {os.path.join(bucket, key): (bucket, key) for bucket, key in bucket_key_tuples}
    bucket_key_tuples_deduped = list(bucket_key_dict.values())
    return bucket_key_tuples_deduped

def process_s3_file(bucket, key):
    '''
    Reads JSON newline file from S3 bucket and return it as an array of
    dictionary objects

	Parameters:
		bucket: S3 bucket of the file you want to read
        key: S3 key of the file you want to read

	Returns:
		list of dictionary objects
    '''
    s3_client = boto3.client('s3')
    s3_obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = s3_obj['Body'].read()
    lines = data.splitlines()
    raw_recs = [json.loads(i) for i in lines]
    return raw_recs

def flatten_dict(d, json_string_fields):
    '''
    Flattens nested dictionary object. Key for nested fields will be all of its
    parent fields concatenated by '_'. For example:
    {'level1': {'level2': {'level3': 'hello'}, 'level2.2': 'hey'}} will become
    {'level1_level2_level3': 'hello', 'level1_level2.2': 'hey'}

	Parameters:
		d: nested dictionary object to be flattened
        json_string_fields: list of field names indicating nested dictionary
            fields that should be stringified instead of getting flattened further

	Returns:
		flattened dictionary object
    '''
    def expand(key, value):
        if isinstance(value, dict):
            if len(value.items()) == 1 and list(value.values())[0] == None:
                return [ (key, list(value.keys())[0])]
            elif key in json_string_fields:
                return [(key, json.dumps(value))]
            else:
                return [ (key + '_' + k, v) for k, v in flatten_dict(value, json_string_fields).items() ]
        else:
            return [ (key, value) ]

    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def process_raw_recs(raw_rec, rename_prefix_fields=[], rename_fields=[],
                     int_fields=[], json_string_fields=[]):
    '''
    Performs various common data transformation needed to prepare records for
    the Socrata platform, including:
    1) Flatten the data structure
    2) Rename certain field prefixes to achieve consistency across data sets
    3) Rename certain fields to achieve consistency across data sets
    4) Set certain fields as integers
    5) Stringify selected complex object fields

	Parameters:
		raw_rec: raw dictionary object
        rename_prefix_fields: list of (original_field_prefix, new_field_prefix) tuples
        rename_fields: list of (original_field_name, new_field_name) tuples
        int_fields: list of fields that should be transformed into integer fields
        json_string_fields: list of field names indicating fields that should be
         stringified instead of getting flattened further

	Returns:
		transformed dictionary object
    '''
    # order of operation: rename prefix, rename fields, stringify json fields
    out = flatten_dict(raw_rec, json_string_fields)

    for old_prefix, new_prefix in rename_prefix_fields:
        out = {k.replace(old_prefix, new_prefix) if old_prefix in k else k: v
               for k,v in out.items()}

    for old_f, new_f in rename_fields:
        if old_f in out:
            out[new_f] = copy.deepcopy(out[old_f])
            del out[old_f]

    out = {k: int(v) if k in int_fields else v for k,v in out.items()}
    out = {k: json.dumps(v) if k in json_string_fields else v for k,v in out.items()}
    return out

def get_col_dtype_dict(socrata_client, dataset_id):
    '''
    Retrieve data dictionary of a Socrata data set in the form of a dictionary,
    with the key being the column name and the value being the column data type

	Parameters:
		socrata_client: connected sodapy Socrata client
        dataset_id: ID of Socrata data set

	Returns:
		data dictionary of a Socrata data set in the form of a dictionary,
        with the key being the column name and the value being the column data type
    '''
    dataset_col_meta = socrata_client.get_metadata(dataset_id)['columns']
    col_dtype_dict = {col['name']: col['dataTypeName'] for col in dataset_col_meta}
    return col_dtype_dict

def mod_dtype(rec, col_dtype_dict, float_fields=[]):
    '''
    Make sure the data type of each field in the data record matches the data type
    of the field in the Socrata data set.

	Parameters:
		rec: dictionary object of the data record
        col_dtype_dict: data dictionary of a Socrata data set in the form of a dictionary,
        with the key being the column name and the value being the column data type
        float_fields: list of fields that should be a float

	Returns:
		dictionary object of the data record, with number, string, and boolean fields
        modified to align with the data type of the corresponding Socrata data set
    '''
    identity = lambda x: x
    dtype_func = {'number': float, 'text': str, 'checkbox': bool}
    out = {}
    for k,v in rec.items():
        if k in float_fields and k in col_dtype_dict:
            out[k] = float(v)
        elif k in col_dtype_dict:
            out[k] = dtype_func.get(col_dtype_dict.get(k, 'j'), identity)(v)
    return out
