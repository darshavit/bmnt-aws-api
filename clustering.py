import sys
import os
from airtable import Airtable
import numpy as np
import scipy.io as sio
import csv
import pickle
from octave_analytics import clustering

def generate_data_for_field(name, records, id_to_fields, id_list):
	'''
	- name: field name to generate data for
	- records: matching records for query, or just a list of records
	- id_to_fields: problem_id to database fields
	- id_list: list of problem_ids
	'''
	num_unique = 0
	mapping_dict = {}
	for record in records:
		labels = record['fields'][name]
		for label in labels:
			if label not in mapping_dict:
				mapping_dict[label] = num_unique
				num_unique += 1
	matrix = np.zeros((num_unique, len(id_list)))
	for i in range(len(id_list)):
		labels = id_to_fields[id_list[i]][name]
		for label in labels:
			matrix[mapping_dict[label],i] = 1

	return matrix

def perform_clustering(problem_id_to_fields, matching_records, ELEMENTS=True, PROCESSES=True,
							DATA=False, PROGRAM=False, ROLES=False):

	problem_id_list = []
	for record in matching_records:
		problem_id_list.append(int(record['fields']['problem_id']))
	problem_id_list = np.array(problem_id_list)

	all_data = []

	if ELEMENTS:
		elements_matrix = generate_data_for_field('elements', matching_records,
												problem_id_to_fields, problem_id_list)
		all_data.append(elements_matrix)
	if PROCESSES:
		process_matrix = generate_data_for_field('processes', matching_records, 
													problem_id_to_fields, problem_id_list)
		all_data.append(process_matrix)
	if DATA:
		data_matrix = generate_data_for_field('data', matching_records,
												problem_id_to_fields, problem_id_list)
		all_data.append(data_matrix)
	if PROGRAM:
		program_matrix = generate_data_for_field('program', matching_records,
													problem_id_to_fields, problem_id_list)
		all_data.append(program_matrix)
	if ROLES:
		roles_matrix = generate_data_for_field('roles', matching_records,
													problem_id_to_fields, problem_id_list)
		all_data.append(roles_matrix)

	num_features = 0
	for mat in all_data:
		num_features += mat.shape[0]

	all_data_matrix = np.zeros((num_features, len(problem_id_list)))
	current_offest = 0 
	for mat in all_data:
		nfs = mat.shape[0]
		all_data_matrix[current_offest:current_offest+nfs,:] = mat
		current_offest += nfs
	c = input ('Would you like to see a dendogram for all the problems? [y/n]\n')
	show_dendo = False
	if c == 'y':
		show_dendo = True

	Zlklb, clusters = clustering(all_data_matrix, problem_id_list, show_dendo)
	return Zlklb, clusters

# This function will generate a csv matrix that contains data
# in the format Problem x elements
def generate_tableau_files(matching_records, source):
	template_doc = None
	key = None
	if source == 'data':
		template_doc = 'template_elements_data.csv'
		key = 'data'
	elif source == 'process':
		template_doc = 'template_elements_process.csv'
		key = 'processes'
	else:
		print('Invalid source provided: {}'.format(source))
		return

	all_pairs_count = {}
	for record in matching_records:
		elements = record['fields']['elements']
		if key not in record['fields']:
			continue
		other = record['fields'][key]

		for j in elements:
			for o in other:
				j_ = j.strip()
				o_ = o.strip()
				j_o_ = (j_,o_)
				if j_o_ not in all_pairs_count:
					all_pairs_count[j_o_] = 0
				all_pairs_count[j_o_] += 1

	with open(template_doc, 'r') as csv_read_file:
		docreader = csv.reader(csv_read_file)
		with open('ELEMENTS_' + source.upper() + '.csv', 'w') as csv_write_file:
			docwriter = csv.writer(csv_write_file)
			for line in docreader:
				key_tuple = (line[0].strip(), line[1].strip())
				if key_tuple in all_pairs_count:
					line[2] = str(all_pairs_count[key_tuple])
				else:
					line[2] = str(0)
				docwriter.writerow(line)

	print('Finished writing ELEMENTS_' + source.upper() + '.csv')

# These should be moved to a .env file for security in the future
BASE_KEY = 'appHXQWL4nSnCyifT'
API_KEY = 'key3tgXMZ5FNkZZ98'
TABLE_ID = 'tblhqeLMkgizweQfk'

fields_to_search = {
	'problem_title': None,
	'problem_statement': None,
	'sponsor_name': None,
	'sponsor_title': None,
	'sponsor_email': None,
	'sponsor_org': None,
	'program': None,
	'elements': None,
	'setting': None,
	'roles': None,
	'processes': None,
	'data': None,
	'employee_sourced_curated': None
}
# Format searchable fields into a pretty string for display
all_fields = '\n'.join(list(fields_to_search.keys()))
# Create the airtable instance for the Problem table
airtable = Airtable(BASE_KEY, TABLE_ID, api_key=API_KEY)

# Instruct the user how to use this script
print('##### Successfully Connected to Problem table in Airtable #####\n\n')
print('#############################################################################')
print('#############################################################################')
print('Fields that are included in the search include:\n\n{}'.format(all_fields))
print('#############################################################################\n')
print('Usage: This script will execute a search based on the field values provided.\nA minimum of 1 field_name and associated field_value is expected')
print('The expected format for user provided input is\n <field_name_1>=<field_value_1>;<field_name_2>=<field_value_2>;...')
print('An example query: \n program=ONR;elements=Buy Capability, Improve Planning;data=HR Data')
print('#############################################################################\n')

# Get the query params from the user via stdin 
query_parameter_string = input('Please input your search criteria (semi-colon seperated list of field_names and field_values)\n')
# Convert to lower case
query_parameter_string = query_parameter_string.lower()
# split by semi-colon
query_parameters = query_parameter_string.split(';')

for param in query_parameters:
	field, value = param.split('=')
	if field not in fields_to_search:
		print('{} is currently not a supported searchable field. Skipping')
		continue
	if ',' in value:
		value = value.split(',')
	# print('Including "{}" with value "{}" as part of the search'.format(field, value))
	fields_to_search[field] = value

search_statements = []

for field in fields_to_search:
	value = fields_to_search[field]
	# Actually provided value for this field
	if value is not None:
		# Check to see if list
		if type(value) is list:
			for it in value:
				it = it.strip()
				search_statements.append("SEARCH('%s', LOWER({%s})) > 0" % (it, field))
		elif type(value) is str:
			value = value.strip()
			search_statements.append("SEARCH('%s', LOWER({%s})) > 0" % (value, field))
formula = "" # Dar look at this 
if len(search_statements) == 0:
	print('Error in constructing the search query, please make sure you spell the field_names correctly, and that they are available as search parameters')
else:
	search_type = input('Please enter "s" for a strict search, or "l" for a loose search\n' + \
						'strict: The returned records will match ALL of the tags/labels you specified\n' + \
						'loose: If any of the tags/labels specified is found in a record, it will be returned\n')
	if search_type == 's': # Dar look at this 
		formula = "AND(" + ','.join(search_statements) + ")" # Dar look at this 
		formula = "OR(" + ','.join(search_statements) + ")" # Dar look at this 

matching_records = airtable.get_all(filterByFormula=formula)

if len(matching_records) == 0:
	print('######################################## WARNING ########################################')
	print('No Results were found for the provided parameters \nPlease Check the query_parameters to make sure everything is spelled correctly, or try a different query')
	print('Query Params: {}'.format(query_parameters))
else:
	# First get list of problem numbers
	problem_id_to_fields = {}
	for record in matching_records:
		problem_id_to_fields[record['fields']['problem_id']] = record['fields']

	print('######################################## SUCCESS ########################################')
	print('Found {} matching records for the search parameters'.format(len(matching_records)))
	count = 0
	for record in matching_records:
		if count % 10 == 0:
			flag = input('Press "c" to continue viewing results, or "q" to move to file generation\n')
			if flag == 'c':
				start = count + 1
				finish = count + 11 if count + 11 < len(matching_records) else len(matching_records)
				print("Showing results {} to {}".format(start, finish))
			else:
				break
		count += 1
		title = record['fields']['problem_title'] if 'problem_title' in record else None
		problem_statement = record['fields']['problem_statement'] if 'problem_statement' in record else None
		elements = record['fields']['elements'] if 'elements' in record['fields'] else None
		process = record['fields']['processes'] if 'processes' in record['fields'] else None
		data = record['fields']['data'] if 'data' in record['fields'] else None
		print('------------------------------------------------------------')
		print('Title: {}'.format(title))
		print('Problem Statement: {}'.format(problem_statement))
		print('Elements: {}'.format(elements))
		print('Processes: {}'.format(process))
		print('Data: {}\n'.format(data))
		print('------------------------------------------------------------')

	x = input('Please type "c" to for clustering "t" to generate a .csv file for tableau, "b" to generate both, or anything else to quit\n')
	x = x.strip()
	if x == 'c' or x == 'clustering':
		flags = input("Please indicate which data to use. You can combine multiple by providing multiple letters\n"\
						"'e'=elements\n"\
						"'p'=processes\n"\
					 	"'d'=data\n"\
					 	"'g'=program\n"\
					 	"'r'=roles\n")
		ELEMENTS = True if 'e' in flags else False
		PROCESSES = True if 'p' in flags else False
		DATA = True if 'd' in flags else False
		PROGRAM = True if 'g' in flags else False
		ROLES = True if 'r' in flags else False
		Zlklb, clusters = perform_clustering(problem_id_to_fields, matching_records, ELEMENTS=ELEMENTS, PROCESSES=PROCESSES, DATA=DATA, PROGRAM=PROGRAM, ROLES=ROLES)
		num_clusters = sum([type(l) == type(list()) for l in clusters])
		num_singletons = len(clusters) - num_clusters
		num_problems = Zlklb.shape[0] + 1
		c = input('Generated {} clusters and {} singleton problems from {} total. Enter "v" to view results by cluster, or "c" to continue\n'.format(num_clusters, num_singletons, num_problems))
		if c == 'v':
			count = 1
			for i in range(len(clusters)):
				c = input ("Enter 'c' to continue viewing clusters, or 'q' to continue\n")
				if c == 'q':
					break
				if type(clusters[i]) == type(list()):
					print('######################## Cluster {} ########################'.format(count))
					print('############### Problems {} - {} of {} total ###############'.format(count, count + len(clusters[i])-1, num_problems))
					print('##### Problem Ids: {} #####'.format([int(it) for it in clusters[i]]))
					count += len(clusters[i])
					for it in clusters[i]:
						record = problem_id_to_fields[int(it)]
						title = record['problem_title'] if 'problem_title' in record else None
						problem_statement = record['problem_statement'] if 'problem_statement' in record else None
						program = record['program'] if 'program' in record else None
						sponsor_org = record['sponsor_org'] if 'sponsor_org' in record else None
						sponsor_name = record ['sponsor_name'] if 'sponsor_name' in record else None
						sponsor_title = record ['sponsor_title'] if 'sponsor_title' in record else None
						print('------------------------------------------------------------')
						print('Title: {}'.format(title))
						print('Sponsoring Organization: {}'.format(program))
						print('Sponsoring Organization: {}'.format(sponsor_org))
						print('Problem Statement: {}'.format(problem_statement))
						print('Point of Contact: {}'.format(sponsor_name))
						print('Point of Contact Title: {}'.format(sponsor_title))
						print('------------------------------------------------------------')
				else:
					print('####################### Singleton {} #######################'.format(count))
					print('################## Problem {} of {} total ##################'.format(count, num_problems))
					count += 1
					record = problem_id_to_fields[int(it)]
					title = record['problem_title'] if 'problem_title' in record else None
					problem_statement = record['problem_statement'] if 'problem_statement' in record else None
					sponsor_org = record['sponsor_org'] if 'sponsor_org' in record else None
					program = record['program'] if 'program' in record else None
					sponsor_name = record ['sponsor_name'] if 'sponsor_name' in record else None
					sponsor_title = record ['sponsor_title'] if 'sponsor_title' in record else None
					print('------------------------------------------------------------')
					print('Title: {}'.format(title))
					print('Sponsoring Organization: {}'.format(program))
					print('Sponsoring Organization: {}'.format(sponsor_org))
					print('Problem Statement: {}'.format(problem_statement))
					print('Point of Contact: {}'.format(sponsor_name))
					print('Point of Contact Title: {}'.format(sponsor_title))
					print('------------------------------------------------------------')

	elif x == 't' or x == 'tableau':
		flag = input('Input "1" to create ELEMENTS_DATA.csv, "2" to create ELEMENTS _PROCESS.csv, or "3" to create both\n')
		if flag == '1' or flag == '3':
			generate_tableau_files(matching_records, 'data')
		if flag == '2' or flag == '3':
			generate_tableau_files(matching_records, 'process')
	elif x == 'b' or x == 'both':
		flag = input('Input "1" to create ELEMENTS _DATA.csv, "2" to create ELEMENTS _PROCESS.csv, or "3" to create both\n')
		if flag == '1' or flag == '3':
			generate_tableau_files(matching_records, 'data')
		if flag == '2' or flag == '3':
			generate_tableau_files(matching_records, 'process')
		flags = input("Please indicate which data to use. You can combine multiple by providing multiple letters\n"\
						"'e'=elements\n"\
						"'p'=processes\n"\
					 	"'d'=data\n"\
					 	"'g'=program\n"\
					 	"'r'=roles\n")
		ELEMENTS = True if 'j' in flags else False
		PROCESSES = True if 'p' in flags else False
		DATA = True if 'd' in flags else False
		PROGRAM = True if 'g' in flags else False
		ROLES = True if 'r' in flags else False
		Zlklb, clusters = perform_clustering(problem_id_to_fields, matching_records, ELEMENTS =ELEMENTS , PROCESSES=PROCESSES, DATA=DATA, PROGRAM=PROGRAM, ROLES=ROLES)
		num_clusters = sum([type(l) == type(list()) for l in clusters])
		num_singletons = len(clusters) - num_clusters
		num_problems = Zlklb.shape[0] + 2
		c = input('Generated {} clusters and {} singleton problems from {} total. Enter "v" to view results by cluster, or "c" to continue\n'.format(num_clusters, num_singletons, num_problems))
		if c == 'v':
			count = 1
			for i in range(len(clusters)):
				c = input ("Enter 'c' to continue viewing clusters, or 'q' to continue\n")
				if c == 'q':
					break
				if type(clusters[i]) == type(list()):
					print('######################## Cluster {} ########################'.format(count))
					print('############### Problems {} - {} of {} total ###############'.format(count, count + len(clusters[i])-1, num_problems))
					print('##### Problem Ids: {} #####'.format([int(it) for it in clusters[i]]))
					count += len(clusters[i])
					for it in clusters[i]:
						record = problem_id_to_fields[int(it)]
						title = record['problem_title'] if 'problem_title' in record else None
						problem_statement = record['problem_statement'] if 'problem_statement' in record else None
						sponsor_org = record['sponsor_org'] if 'sponsor_org' in record else None
						program = record['program'] if 'program' in record else None
						sponsor_name = record ['sponsor_name'] if 'sponsor_name' in record else None
						sponsor_title = record ['sponsor_title'] if 'sponsor_title' in record else None
						print('------------------------------------------------------------')
						print('Title: {}'.format(title))
						print('Sponsoring Organization: {}'.format(program))
						print('Sponsoring Organization: {}'.format(sponsor_org))
						print('Problem Statement: {}'.format(problem_statement))
						print('Point of Contact: {}'.format(sponsor_name))
						print('Point of Contact Title: {}'.format(sponsor_title))
						print('------------------------------------------------------------')
				else:
					print('####################### Singleton {} #######################'.format(count))
					print('################## Problem {} of {} total ##################'.format(count, num_problems))
					count += 1
					record = problem_id_to_fields[int(it)]
					title = record['problem_title'] if 'problem_title' in record else None
					problem_statement = record['problem_statement'] if 'problem_statement' in record else None
					sponsor_org = record['sponsor_org'] if 'sponsor_org' in record else None
					program = record['program'] if 'program' in record else None
					sponsor_name = record ['sponsor_name'] if 'sponsor_name' in record else None
					sponsor_title = record ['sponsor_title'] if 'sponsor_title' in record else None
					print('------------------------------------------------------------')
					print('Title: {}'.format(title))
					print('Sponsoring Organization: {}'.format(program))
					print('Sponsoring Organization: {}'.format(sponsor_org))
					print('Problem Statement: {}'.format(problem_statement))
					print('Point of Contact: {}'.format(sponsor_name))
					print('Point of Contact Title: {}'.format(sponsor_title))
					print('------------------------------------------------------------')

	else:
		print('Not writing any files. Done')





