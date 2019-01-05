'''Write record to data lake'''

import json
import logging
import os

import boto3
import iso8601

log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.root.setLevel(logging.getLevelName(log_level))  # type: ignore
_logger = logging.getLogger(__name__)

DATA_LAKE_S3_BUCKET = os.environ.get('DATA_LAKE_S3_BUCKET')

S3_CLIENT = boto3.client('s3')

boto3.resource('dynamodb')
DDB_DESERIALIZER = boto3.dynamodb.types.TypeDeserializer()

def _get_s3_key(record):
    '''Get S3 key based on line item info.'''
    dt = iso8601.parse_date(record.get('RequestTime'))
    ride_id = record.get('RideId')

    # FIXME: We need to ensure that this results in truly unique objects.
    s3_key = 'year={year}/month={month}/day={day}/{ride_id}.json'.format(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        ride_id=ride_id
    )

    return s3_key


def _transform_ddb_item(d: dict, deserializer=DDB_DESERIALIZER):
    '''Transform DDB record for data lake'''
    return {k: deserializer.deserialize(v) for k,v in d.items()}

def _get_record_ddb_item(d: dict):
    '''Get DDB item from record'''
    record_item = d.get('dynamodb').get('NewImage')
    ddb_item = _transform_ddb_item(record_item)
    return ddb_item


def _write_record_to_s3(record: dict, s3_bucket:str=DATA_LAKE_S3_BUCKET) -> dict:
    '''Write record to S3'''
    s3_key = _get_s3_key(record)
    resp = S3_CLIENT.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=json.dumps(record)
    )

    return resp


def handler(event, context):
    '''Function entry'''
    _logger.info('Event: {}'.format(json.dumps(event)))

    for record in event.get('Records'):
        if record.get('eventName') == 'INSERT':
            data_lake_record = _get_record_ddb_item(record)
            _write_record_to_s3(data_lake_record)

    resp = {}
    _logger.info('Response: {}'.format(json.dumps(resp)))
    return resp

