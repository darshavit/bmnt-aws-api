import json
import os
import constants
import logging
import datetime
from airtable import Airtable

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_data_from_airtable(data, all_fields, table_name, form, required_fields=None):
    cleaned_data = {}
    for field, value in data.items():
        # Make sure field is valid
        if field[3:] not in all_fields:
            logger.warning(constants.INVALID_FIELD.format(field[3:], table_name))
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': constants.INVALID_FIELD.format(field[3:], table_name),
                    'received_data': data
                })
            }
        # Make sure required field is not empty
        if required_fields is not None:
            if field[3:] in required_fields:
                if not value:
                    logger.warning(constants.REQUIRED_FIELD_IS_NULL.format(field[3:], form))
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'message': constants.REQUIRED_FIELD_IS_NULL.format(field[3:], form),
                            'received_data': data
                        })
                    }
        cleaned_data[field[3:]] = value
    return cleaned_data


def submit_to_airtable(data, table_name):
    logger.info('## Attempting to submit to {} Table. data: {}'.format(table_name, data))
    table = Airtable(constants.AIRTABLE_BASE_KEY, table_name, api_key=os.environ['AIRTABLE_KEY'])
    rec = table.insert(data)
    if 'id' not in rec:
        logger.warning(constants.UNABLE_TO_CREATE_RECORD.format(rec))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': constants.UNABLE_TO_CREATE_RECORD.format(rec),
                'received_data': data
            })
        }
    logger.info('## Successfully submitted to {} Table. New id: {}'.format(table_name, rec['id']))
    return rec


def sourced_problem_handler(event, context):
    logger.info('## Processing sourced problem submit')
    raw_data = event['body']

    ################# PROBLEM TABLE SUBMIT #################
    data_problem = check_data_from_airtable(raw_data,
                                    constants.ALL_SOURCED_FIELDS,
                                    'Problems',
                                    'sourced problem',
                                    constants.REQUIRED_SOURCED_FIELDS)
    if 'statusCode' in data_problem:
        logger.warning(data_problem['body'])
        return data_problem

    rec_problem = submit_to_airtable(data_problem, 'Problems')
    if 'id' not in rec_problem:
        return rec_problem
    new_problem_id = rec_problem['id']
    ################# PROBLEM TABLE SUBMIT #################

    ################# PROBLEM HISTORY TABLE SUBMIT #################
    data_problem_history = {
        'Problem Statement': data_problem['problem_statement'],
        'State': 'Sourced (no BMNT)',
        'Problem ID': [new_problem_id],
        'Pipeline Stage': 'Source'
    }
    rec_problem_history = submit_to_airtable(data_problem_history, 'Problem History')
    if 'id' not in rec_problem_history:
        return rec_problem_history
    new_problem_history_id = rec_problem_history['id']
    ################# PROBLEM HISTORY TABLE SUBMIT #################

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'sourced problem'
        })
    }


def curated_problem_handler(event, context):
    logger.info('## Processing curated problem submit')
    raw_data = event['body']

    ################# PROBLEM TABLE SUBMIT #################
    data_problem = check_data_from_airtable(raw_data,
                                            constants.ALL_CURATED_UPDATED_FIELDS,
                                            'Problems',
                                            'sourced problem',
                                            constants.REQUIRED_CURATED_FIELDS)
    data_problem.pop('State')
    if 'statusCode' in data_problem:
        logger.warning(data_problem['body'])
        return data_problem

    rec_problem = submit_to_airtable(data_problem, 'Problems')
    if 'id' not in rec_problem:
        return rec_problem
    new_problem_id = rec_problem['id']
    ################# PROBLEM TABLE SUBMIT #################

    ################# PROBLEM HISTORY TABLE SUBMIT #################
    data_problem_history = {
        'Problem Statement': data_problem['problem_statement'],
        'State': raw_data['cp_State'],
        'Problem ID': [new_problem_id],
        'Pipeline Stage': constants.STATE_TO_PIPELINE[raw_data['cp_State']],
        'date_curated': str(datetime.date.today())
    }
    rec_problem_history = submit_to_airtable(data_problem_history, 'Problem History')
    if 'id' not in rec_problem_history:
        return rec_problem_history
    new_problem_history_id = rec_problem_history['id']
    ################# PROBLEM HISTORY TABLE SUBMIT #################
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "curated problem"
        })
    }


def updated_problem_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "updated problem"
        })
    }
