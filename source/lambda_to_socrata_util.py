import boto3
import copy
import itertools
import json
import os


def get_fps_from_event(event):
    bucket_key_tuples = [(e['s3']['bucket']['name'], e['s3']['object']['key']) for e in event['Records']]
    bucket_key_dict = {os.path.join(bucket, key): (bucket, key) for bucket, key in bucket_key_tuples}
    bucket_key_tuples_deduped = list(bucket_key_dict.values())
    return bucket_key_tuples_deduped

def process_s3_file(bucket, key):
    s3_client = boto3.client('s3')
    s3_obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = s3_obj['Body'].read()
    lines = data.splitlines()
    raw_recs = [json.loads(i) for i in lines]
    return raw_recs

def flatten_dict(d):
    def expand(key, value):
        if isinstance(value, dict):
            if len(value.items()) == 1 and list(value.values())[0] == None:
                return [ (key, list(value.keys())[0])]
            else:
                return [ (key + '_' + k, v) for k, v in flatten_dict(value).items() ]
        else:
            return [ (key, value) ]

    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def process_raw_recs(raw_rec, rename_prefix_fields=[], rename_fields=[],
                     int_fields=[], json_string_fields=[]):
    out = flatten_dict(raw_rec)

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
    dataset_col_meta = socrata_client.get_metadata(dataset_id)['columns']
    col_dtype_dict = {col['name']: col['dataTypeName'] for col in dataset_col_meta}
    return col_dtype_dict

def mod_dtype(rec, col_dtype_dict):
    identity = lambda x: x
    dtype_func = {'number': int, 'text': str}
    out = {k: dtype_func.get(col_dtype_dict.get(k, 'j'), identity)(v)
           for k,v in rec.items()
           if k in col_dtype_dict}
    return out
