import json
import os
import constants
import logging
import datetime
from airtable import Airtable

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_data_from_retool(data, all_fields, table_name, form, required_fields=None):
    """
    Serves as a sanity check for the data from a retool form.

    :param data: data to clean (directly from retool form)
    :param all_fields: all fields for this problem (sourced/curated fields)
    :param table_name: table to check for (Table within Airtable)
    :param form: which form it came from (sourced/curated/updated)
    :param required_fields: required fields for form
    :return: on success returns well formatted data, on error returns error message
    """
    cleaned_data = {}
    logger.info('## Checking Retool Data')
    for field, value in data.items():
        # Make sure field is valid
        if field not in all_fields:
            logger.warning(constants.INVALID_FIELD.format(field, table_name))
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': constants.INVALID_FIELD.format(field, table_name),
                    'received_data': data
                })
            }
        # Make sure required field is not empty
        if required_fields is not None:
            if field in required_fields:
                if not value:
                    logger.warning(constants.REQUIRED_FIELD_IS_NULL.format(field, form))
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'message': constants.REQUIRED_FIELD_IS_NULL.format(field, form),
                            'received_data': data
                        })
                    }
        cleaned_data[field] = value
    logger.info('## The Received data is well formatted for airtable. Data: {}'.format(cleaned_data))
    return cleaned_data


def submit_to_airtable(data, table_name):
    """
    Wrapper function to submit to airtable
    :param data: data to submit
    :param table_name: table to submit to
    :return: on success returns new entry, on error returns error message
    """
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


def update_in_airtable(rec_id, table_name, data):
    """
    wrapper function to update a record in airtable
    :param rec_id: record to update
    :param table_name: table to update in
    :param data: data to add/adjust
    :return: on success returns updated entry, on error returns error message
    """
    logger.info('## Attempting to update rec_id {} in table {} with data {}'.format(rec_id, table_name, data))
    table = Airtable(constants.AIRTABLE_BASE_KEY, table_name, api_key=os.environ['AIRTABLE_KEY'])
    updated_rec = table.update(rec_id, data)
    if 'id' not in updated_rec:
        logger.warning(constants.UNABLE_TO_UPDATE_RECORD.format(rec_id, updated_rec))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': constants.UNABLE_TO_UPDATE_RECORD.format(rec_id, updated_rec),
                'received_date': data
            })
        }
    logger.info('## Successfully updated record {} in table {}'.format(rec_id, table_name))
    return updated_rec


def delete_from_airtable(rec_id, table_name):
    """
    wrapper function to delete a record in airtable
    :param rec_id: the record to delete
    :param table_name: from this table
    """
    logger.info('## Deleting {} from {}'.format(rec_id, table_name))
    table = Airtable(constants.AIRTABLE_BASE_KEY, table_name, api_key=os.environ['AIRTABLE_KEY'])
    table.delete(rec_id)
    logger.info('## Deleted Successfully')


def submit_to_problem_table(data, problem_type):
    """
    Wrapper function to submit data to problem table
    :param data: data to submit
    :param problem_type: sourced/curated
    :return: on success returns (True, new_entry), on error returns (False, err_msg)
    """
    data_problem = check_data_from_retool(data,
                                          constants.ALL_FIELDS[problem_type],
                                          'Problems',
                                          problem_type,
                                          constants.REQUIRED_FIELDS[problem_type])

    if 'statusCode' in data_problem:
        return False, data_problem

    rec_problem = submit_to_airtable(data_problem, 'Problems')
    if 'statusCode' in rec_problem:
        return False, rec_problem

    return True, rec_problem


def submit_to_problem_history_table(data, problem_id, problem_type):
    data_problem_history = {
        'Problem Statement': data['problem_statement'],
        'Problem ID': problem_id
    }
    if problem_type is 'sourced':
        data_problem_history['State'] = 'Sourced (no BMNT)'
        data_problem_history['Pipeline Stage'] = constants.STATE_TO_PIPELINE['Sourced (no BMNT)']
    elif problem_type is 'curated':
        data_problem_history['State'] = data['State']
        data_problem_history['Pipeline Stage'] = constants.STATE_TO_PIPELINE[data['State']]

    rec_problem_history = submit_to_airtable(data_problem_history, 'Problem History')
    if 'statusCode' in rec_problem_history:
        return False, rec_problem_history

    return True, rec_problem_history


def handle_subgroup_logic(data, problem_id):
    subgroup_table = Airtable(constants.AIRTABLE_BASE_KEY, 'Sub Group', api_key=os.environ['AIRTABLE_KEY'])

    # Existing subgroup
    if 'sponsor_subgroup' in data:
        logger.info('Using existing subgroup {}'.format(data['sponsor_subgroup']))
        existing_subgroup_data = subgroup_table.get(data['sponsor_subgroup'])
        subgroup_update_data = {}

        if 'Problems' in existing_subgroup_data:
            subgroup_update_data['Problems'] = existing_subgroup_data['Problems'].append(problem_id)
        else:
            subgroup_update_data['Problems'] = [problem_id]
        rec_subgroup = update_in_airtable(existing_subgroup_data['id'], 'Sub Group', subgroup_update_data)
        if 'statusCode' in rec_subgroup:
            return False, rec_subgroup

        problem_update_data = {'physical_location': existing_subgroup_data['id']}
        if 'Group' in existing_subgroup_data:
            problem_update_data['Group'] = existing_subgroup_data['Group']
        if 'Organization' in existing_subgroup_data:
            problem_update_data['Organization'] = existing_subgroup_data['Organization']

        # Update problem to include these links
        rec_problem = update_in_airtable(problem_id, 'Problems', problem_update_data)
        if 'statusCode' in rec_problem:
            return False, rec_problem
        return True, existing_subgroup_data

    # New subgroup entry
    elif data['sponsor_org']:
        logger.info('Creating new subgroup entry: {}'.format(data['sponsor_org']))
        data_subgroup = {
            'Name': data['sp_sponsor_org'],
            'Problems': [problem_id]
        }
        if data['physical_location']:
            if ',' in data['physical_location']:
                city, state = data['physical_location'].split()
                if city:
                    data_subgroup['City'] = city
                if state:
                    data_subgroup['State'] = state
            elif '-' in data['sp_physical_location']:
                data_subgroup['State'] = data['physical_location']
        rec_subgroup = submit_to_airtable(data_subgroup, 'Sub Group')
        if 'statusCode' in rec_subgroup:
            return False, rec_subgroup
        rec_problem = update_in_airtable(problem_id, 'Problems', {'physical_location': rec_subgroup['id']})
        if 'statusCode' in rec_problem:
            return False, rec_problem

        return True, rec_subgroup


def submit_problem_handler(event, context):
    """
    Executes the logic for submitting a new problem
        1. Submits a new entry to the Problem table with the data provided
        2. Creates a new Problem History entry for the newly created problem
        3. Checks to see if the
    :param event:
    :param context:
    :return: on success returns a summary of new entries, on error returns error message
    """
    raw_data = event['body']
    problem_type = raw_data['problem_type']

    # Problem Table Submit
    success, rec_problem = submit_to_problem_table(raw_data, problem_type)
    if not success:
        return rec_problem

    # Problem History Submit
    success, rec_problem_history = submit_to_problem_history_table(raw_data, rec_problem['id'], problem_type)
    if not success:
        delete_from_airtable(rec_problem['id'], 'Problems')
        return rec_problem_history
    ################# PROBLEM HISTORY TABLE SUBMIT #################

    ################# SUB GROUP TABLE LOGIC #################
    subgroup_table = Airtable(constants.AIRTABLE_BASE_KEY, 'Sub Group', api_key=os.environ['AIRTABLE_KEY'])
    # Subgroup already exists
    if raw_data['sponsor_subgroup']:
        logger.info('Using existing subgroup {}'.format(raw_data['sponsor_subgroup']))
        existing_subgroup_data = subgroup_table.get(raw_data['sponsor_subgroup'])
        subgroup_update_data = {}
        if 'Problems' in existing_subgroup_data:
            subgroup_update_data['Problems'] = existing_subgroup_data['Problems'].append(rec_problem['id'])
        else:
            subgroup_update_data['Problems'] = [rec_problem['id']]
        update_in_airtable(existing_subgroup_data['id'], 'Sub Group', subgroup_update_data)
        problem_update_data = {'physical_location': existing_subgroup_data['id']}
        if 'Group' in existing_subgroup_data:
            problem_update_data['Group'] = existing_subgroup_data['Group']
        if 'Organization' in existing_subgroup_data:
            problem_update_data['Organization'] = existing_subgroup_data['Organization']
        # Update problem to include these links
        rec_problem = update_in_airtable(rec_problem['id'], 'Problems', problem_update_data)
        if 'statusCode' in rec_problem:
            logger.warning(rec_problem['body'])
            return rec_problem
    # New subgroup entry
    elif raw_data['sponsor_org']:
        logger.info('Creating new subgroup entry: {}'.format(raw_data['sponsor_org']))
        data_subgroup = {
            'Name': raw_data['sp_sponsor_org'],
            'Problems': [rec_problem['id']]
        }
        if raw_data['physical_location']:
            if ',' in raw_data['physical_location']:
                city, state = raw_data['physical_location'].split()
                if city:
                    data_subgroup['City'] = city
                if state:
                    data_subgroup['State'] = state
            elif '-' in raw_data['sp_physical_location']:
                data_subgroup['State'] = raw_data['physical_location']
        rec_subgroup = submit_to_airtable(data_subgroup, 'Sub Group')
        if 'statusCode' in rec_subgroup:
            logger.warning(rec_subgroup['body'])
            return rec_subgroup
        rec_problem = update_in_airtable(rec_problem['id'], 'Problems', {'physical_location': rec_subgroup['id']})
        if 'statusCode' in rec_problem:
            logger.warning(rec_subgroup['body'])
            return rec_subgroup
    ################# SUB GROUP TABLE LOGIC #################

    ################# PEOPLE TABLE LOGIC #################
    people_table = Airtable(constants.AIRTABLE_BASE_KEY, 'People', api_key=os.environ['AIRTABLE_KEY'])
    data_people = people_table.search('email', raw_data['sponsor_email'])
    if len(people_table.search('email', raw_data['sponsor_email'])):
        people_update_data = {}
        if 'Problems' in data_people:
            people_update_data['Problems'] = data_people['Problems'].append(rec_problem['id'])
        else:
            people_update_data['Problems'] = [rec_problem['id']]
        update_in_airtable(data_people['id'], 'People', people_update_data)
    else:
        data_people = {}
        if len(raw_data['sponsor_name']) > 1:
            data_people['first_name'] = raw_data['sponsor_name'].split()[0]
            data_people['last_name'] = raw_data['sponsor_name'].split()[1]
        else:
            data_people['first_name'] = raw_data['sponsor_name']
        if 'Organization' in rec_subgroup:
            data_people['Organization'] = rec_subgroup['Organization']
        if 'Group' in rec_subgroup:
            data_people['Group'] = rec_subgroup['Group']
        data_people['Sub Group'] = rec_subgroup['id']
        data_people['Problems'] = [rec_problem['id']]
        if 'sponsor_division' in raw_data:
            data_people['Division'] = raw_data['sponsor_division']


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
    data_problem = check_data_from_retool(raw_data,
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
