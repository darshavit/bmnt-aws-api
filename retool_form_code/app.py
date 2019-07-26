import json
# import requests


def sourced_problem_handler(event, context):

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
