import json
import os
import constants
import logging
import datetime
from airtable import Airtable

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def separate_data(raw_data, problem_type):
    """
    separates the raw data from retool into separate dicts for the various tables
    :param raw_data: data from retool
    :param problem_type: sourced/curated
    :return:
    """
    problem_data = {}
    problem_history_data = {}
    subgroup_data = {}
    people_data = {}

    logger.info('## Organizing Raw data from retool')
    for field, value in raw_data.items():
        if field in constants.ALL_FIELDS[problem_type]:
            problem_data[field] = value
        if field in constants.ALL_FIELDS['problem_history']:
            problem_history_data[field] = value
        if field in constants.ALL_FIELDS['subgroup']:
            subgroup_data[field] = value
        if field in constants.ALL_FIELDS['people']:
            people_data[field] = value
    logger.info('## Organized data by table')
    return problem_data, problem_history_data, subgroup_data, people_data


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
        if required_fields:
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


def determine_data_to_update_for_problem(problem_id, data_new):
    logger.info('## Determining which fields need to be updated for {}'.format(problem_id))
    table = Airtable(constants.AIRTABLE_BASE_KEY, 'Problems', api_key=os.environ['AIRTABLE_KEY'])
    data_old = table.get(problem_id)
    data_to_update = {}
    for field, value in data_new.items():
        if field not in data_old:
            data_to_update[field] = value
        if data_old[field] != data_new[field]:
            data_to_update[field] = value

    if not data_to_update:
        return False, {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'The data provided is no different than the data in Airtable'
            })
        }
    return True, data_to_update


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
        'Problem ID': [problem_id]
    }
    if problem_type == 'sourced':
        data_problem_history['State'] = 'Sourced (no BMNT)'
        data_problem_history['Pipeline Stage'] = constants.STATE_TO_PIPELINE['Sourced (no BMNT)']
        logger.info(data_problem_history)
    elif problem_type == 'curated':
        data_problem_history['State'] = data['State']
        data_problem_history['Pipeline Stage'] = constants.STATE_TO_PIPELINE[data['State']]
        data_problem_history['date_curated'] = str(datetime.date.today())
    else:
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
        # Add Problem to subgroup based on whether subgroup is already associated with problems
        if 'Problems' in existing_subgroup_data['fields']:
            subgroup_update_data['Problems'] = existing_subgroup_data['fields']['Problems']
            if problem_id not in subgroup_update_data['Problems']:
                subgroup_update_data['Problems'].append(problem_id)
        else:
            subgroup_update_data['Problems'] = [problem_id]
        logger.info('Submitting to Airtable')
        rec_subgroup = update_in_airtable(existing_subgroup_data['id'], 'Sub Group', subgroup_update_data)
        if 'statusCode' in rec_subgroup:
            return False, rec_subgroup
        # Add Group and Organization to Problem if needed
        if 'Group' in existing_subgroup_data['fields']:
            problem_update_data = {'Group': existing_subgroup_data['fields']['Group']}
            group_table = Airtable(constants.AIRTABLE_BASE_KEY, 'Group', api_key=os.environ['AIRTABLE_KEY'])
            rec_group = group_table.get(existing_subgroup_data['fields']['Group'][0])
            if 'Organization' in rec_group['fields']:
                problem_update_data['Organization'] = rec_group['fields']['Organization']
            logger.info('Successfully added Group and Org')
            rec_problem = update_in_airtable(problem_id, 'Problems', problem_update_data)
            if 'statusCode' in rec_problem:
                return False, rec_problem
        logger.info('Successfully updated subgroup')
        return True, existing_subgroup_data

    # New subgroup entry
    elif 'sponsor_org' in data:
        logger.info('Creating new subgroup entry: {}'.format(data['sponsor_org']))
        data_subgroup = {
            'Name': data['sponsor_org'],
            'Problems': [problem_id]
        }
        # Handle city,state or international physical location
        if 'physical_location' in data:
            logger.info('adding physical location')
            if ',' in data['physical_location']:
                logger.info('city, state')
                city, state = data['physical_location'].split(',')
                if city:
                    data_subgroup['City'] = city.strip()
                if state:
                    data_subgroup['State'] = state.strip()
            elif '-' in data['sp_physical_location']:
                logger.info('international')
                data_subgroup['State'] = data['physical_location']

        rec_subgroup = submit_to_airtable(data_subgroup, 'Sub Group')
        if 'statusCode' in rec_subgroup:
            return False, rec_subgroup
        return True, rec_subgroup

    return True, None


def handle_people_logic(data, problem_id, rec_subgroup):
    people_table = Airtable(constants.AIRTABLE_BASE_KEY, 'People', api_key=os.environ['AIRTABLE_KEY'])
    data_people = people_table.search('email', data['sponsor_email'])
    # Existing Person
    if len(data_people):
        people_update_data = {}
        logger.info(data_people)
        # Add this problem to this person based on whether they are already associated with problems
        if 'Problems' in data_people[0]['fields']:
            people_update_data['Problems'] = data_people[0]['fields']['Problems']
            if problem_id not in people_update_data['Problems']:
                people_update_data['Problems'].append(problem_id)
            logger.info('Added Problem List to update data')
        else:
            people_update_data['Problems'] = [problem_id]
            logger.info('Created New Problem List for update data')
        # Add subgroup/group/org to person if needed
        if 'Sub Group' in data_people[0]['fields']:
            people_update_data['Sub Group'] = data_people[0]['fields']['Sub Group']
            logger.info('Added sub group to the update data')
            if rec_subgroup['id'] not in data_people[0]['fields']['Sub Group']:
                people_update_data['Sub Group'].append(rec_subgroup['id'])
                logger.info('Added new subgroup to the update data')
            if 'Group' in rec_subgroup['fields']:
                if 'Group' not in data_people[0]['fields']:
                    people_update_data['Group'] = rec_subgroup['fields']['Group']
                    logger.info('Added Group to the update data')
                else:
                    people_update_data['Group'] = data_people[0]['fields']['Group']
                    for grp in rec_subgroup['fields']['Group']:
                        if grp not in people_update_data['Group']:
                            people_update_data['Group'].append(grp)
                    logger.info('Added new groups to the update data')
                group_table = Airtable(constants.AIRTABLE_BASE_KEY, 'Group', api_key=os.environ['AIRTABLE_KEY'])
                if 'Organization' in data_people[0]['fields']:
                    people_update_data['Organization'] = data_people[0]['fields']['Organization']
                    logger.info('Added Organization to the update data')
                else:
                    people_update_data['Organization'] = []
                for grp in people_update_data['Group']:
                    rec_group = group_table.get(grp)
                    if 'Organization' in rec_group['fields']:
                        for org in rec_group['fields']['Organization']:
                            if org not in people_update_data['Organization']:
                                people_update_data['Organization'].append(org)
                        logger.info('Added organization to the update data')
                if not people_update_data['Organization']:
                    people_update_data.pop('Organization')
                    logger.info('Removing organization from update data because there are none')
        rec_people = update_in_airtable(data_people[0]['id'], 'People', people_update_data)
        logger.info('Updated record in airtable: {}'.format(rec_people))
        if 'statusCode' in rec_people:
            return False, rec_people
        return True, rec_people
    else:
        logger.info('Creating new person entry {}'.format(data))
        data_people = {'email': data['sponsor_email']}
        if len(data['sponsor_name'].split(' ', 1)) > 1:
            data_people['first_name'] = data['sponsor_name'].split(' ', 1)[0]
            data_people['last_name'] = data['sponsor_name'].split(' ', 1)[1]
        else:
            data_people['first_name'] = data['sponsor_name']
        if 'Group' in rec_subgroup['fields']:
            data_people['Group'] = rec_subgroup['fields']['Group']
            group_table = Airtable(constants.AIRTABLE_BASE_KEY, 'Group', api_key=os.environ['AIRTABLE_KEY'])
            data_people['Organization'] = []
            for grp in data_people['Group']:
                rec_group = group_table.get(grp)
                if 'Organization' in rec_group['fields']:
                    for org in rec_group['fields']['Organization']:
                        if org not in data_people['Organization']:
                            data_people['Organization'].append(org)

        data_people['Sub Group'] = [rec_subgroup['id']]
        data_people['Problems'] = [problem_id]
        if 'sponsor_division' in data:
            data_people['Division'] = data['sponsor_division']
        rec_people = submit_to_airtable(data_people, 'People')
        logger.info('New person entry {}'.format(rec_people))
        if 'statusCode' in rec_people:
            return False, rec_people
        return True, rec_people


def submit_problem_handler(event, context):
    """
    Executes the logic for submitting a new problem
        1. Submits a new entry to the Problem table with the data provided
        2. Creates a new Problem History entry for the newly created problem
        3. Checks to see if the subgroup exists or not, handles accordingly
        4. Checks to see if the person exists or not, handles accordingly
    :param event:
    :param context:
    :return: on success returns a summary of new entries, on error returns error message
    """
    try:
        raw_data = json.loads(event['body'])['data']
        logger.info('Received data: {}'.format(raw_data))
        if not raw_data:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Somehow, you did not provide any data. Hopefully you are a dev and doing something '
                               'not supported '
                })
            }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'No data given. Error {}'.format(e)
            })
        }

    try:
        problem_type = raw_data['problem_type']
        problem_data, problem_history_data, subgroup_data, people_data = separate_data(raw_data, problem_type)

        # Problem Table Submit
        success, rec_problem = submit_to_problem_table(problem_data, problem_type)
        if not success:
            return rec_problem

        # Problem History Submit
        success, rec_problem_history = submit_to_problem_history_table(problem_history_data, rec_problem['id'], problem_type)
        if not success:
            return rec_problem_history

        # Subgroup Logic
        success, rec_subgroup = handle_subgroup_logic(subgroup_data, rec_problem['id'])
        if not success:
            return rec_subgroup

        # People Logic
        success, rec_people = handle_people_logic(people_data, rec_problem['id'], rec_subgroup)
        if not success:
            return rec_people

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '{} problem submitted successfully!'.format(problem_type),
                'link_problem': '<a href="https://airtable.com/{}/{}"> Link to problem in airtable</a>'.format(
                    constants.PROBLEM_TABLE_ID, rec_problem['id']),
                'link_problem_history': '<a href="https://airtable.com/{}/{}"> Link to problem history table</a>'.format(
                    constants.PROBLEM_HISTORY_TABLE_ID, rec_problem_history['id']),
                'link_subgroup': '<a href="https://airtable.com/{}/{}"> Link to subgroup</a>'.format(
                    constants.SUBGROUP_TABLE_ID, rec_subgroup['id']),
                'link_people': '<a href="https://airtable.com/{}/{}"> Link to person</a>'.format(
                    constants.PEOPLE_TABLE_ID, rec_people['id'])
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Something unexpected went wrong...',
                'error': str(e)
            })
        }


def updated_problem_handler(event, context):
    """
    Executes the logic for updating a problem in airtable
    :param event:
    :param context:
    :return:
    """
    try:
        raw_data = json.loads(event['body']['data'])
        logger.info('Received data was: {}'.format(raw_data))
        if not raw_data:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Somehow, you did not provide any data. Hopefully you are a dev and doing something '
                               'not supported '
                })
            }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'No data given. Error {}'.format(e)
            })
        }

    try:
        problem_id = raw_data['problem_id']
        problem_data, problem_history_data, subgroup_data, people_data = separate_data(raw_data, 'curated')

        # Problem Table, see if there is actually something to update
        success, data_to_update = determine_data_to_update_for_problem(problem_id, problem_data)
        if not success:
            return data_to_update

        # Problem Table submit
        success, updated_problem = update_in_airtable(problem_id, 'Problems', data_to_update)
        if not success:
            return updated_problem

        # Problem History Table
        if 'State' in data_to_update:
            curated = 'updated'
            if raw_data['curated']:
                curated = 'curated'
            success, rec_problem_history = submit_to_problem_history_table(problem_history_data, problem_id, curated)
            if not success:
                return rec_problem_history

        # Handle subgroup if need be
        if 'sponsor_org' in data_to_update:
            logger.info('## Need to update subgroup for problem')
            success, rec_subgroup = handle_subgroup_logic(subgroup_data, problem_id)
            if not success:
                return rec_subgroup

        # Handle people if need be
        if 'sponsor_email' in data_to_update:
            logger.info('## Need to update people for problem')
            success, rec_people = handle_people_logic(people_data, problem_id)
            if not success:
                return rec_people

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Updated problem {} successfully'.format(problem_id),
                'link_problem': '<a href="https://airtable.com/{}/{}"> Link to problem in airtable</a>'.format(
                    constants.PROBLEM_TABLE_ID, problem_id)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Something unexpected went wrong...',
                'error': str(e)
            })
        }
