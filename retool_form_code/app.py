import json
import constants
import requests


def sourced_problem_handler(event, context):
    raw_data = event['body']
    data_problem = {}
    data_problem_history = {}
    data_people = {}
    # convert raw data to formatted data
    for key, value in raw_data.items():
        if key[3:] in constants.REQUIRED_SOURCED_FIELDS:

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "sourced problem"
        })
    }


def curated_problem_handler(event, context):

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
