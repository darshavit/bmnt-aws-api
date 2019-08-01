# Airtable API
AIRTABLE_BASE_KEY = 'appHXQWL4nSnCyifT'
PROBLEM_TABLE_ID = 'tblhqeLMkgizweQfk'
PROBLEM_HISTORY_TABLE_ID = 'tbly11xGCTbbVO0Np'
ORGANIZATION_TABLE_ID = 'tblsQidDARIrdiMoZ'
GROUP_TABLE_ID = 'tblWGBG5AeRcuFtoh'
SUBGROUP_TABLE_ID = 'tblMXektRgNyI186q'
PEOPLE_TABLE_ID = 'tbl7vBHWmZ772lCmH'
DOCUMENTS_TABLE_ID = 'tblAjIzEgR9DMbahK'
TOOL_ANALYTICS_TABLE_ID = 'tblBV4S4sOqwRxcAY'

# Table Fields
ALL_FIELDS = {
    'sourced': ['pre_2019',
                'employee_sourced_curated',
                'program',
                'source_activity',
                'problem_title',
                'problem_statement',
                'background',
                'sponsor_name',
                'sponsor_rank',
                'sponsor_title',
                'sponsor_division',
                'sponsor_org',
                'sponsor_email',
                'senior_leader_name',
                'senior_leader_rank',
                'senior_leader_title',
                'senior_leader_division',
                'senior_leader_email'
                ],
    'curated': ['pre_2019',
                'program',
                'employee_sourced_curated',
                'problem_title',
                'background',
                'problem_statement',
                'beneficiary',
                'basic_need',
                'desired_outcome',
                'constraints',
                'sponsor_name',
                'sponsor_rank',
                'sponsor_title',
                'sponsor_division',
                'sponsor_org',
                'sponsor_email',
                'senior_leader_name',
                'senior_leader_rank',
                'senior_leader_title',
                'senior_leader_division',
                'senior_leader_email',
                'elements',
                'processes',
                'setting',
                'roles',
                'data',
                'team_impact',
                'frequency',
                'cost',
                'humans_impacted',
                'org_threat'
                ],
    'problem_history': ['problem_statement',
                        'State'
                        ],
    'subgroup': ['sponsor_org',
                 'sponsor_subgroup',
                 'physical_location'],
    'people': ['sponsor_email',
               'sponsor_name',
               'sponsor_division'
               ]
}

REQUIRED_FIELDS = {
    'sourced': ['problem_title',
                'problem_statement',
                'sponsor_name',
                'sponsor_email'],
    'curated': ['program',
                'problem_title',
                'problem_statement',
                'sponsor_name',
                'sponsor_email',
                'elements',
                'processes',
                'State']
}

# Sourced Problem Error Responses
INVALID_FIELD = 'Entered invalid field {} for table {}. Please check the data to make sure fields match with airtable'
REQUIRED_FIELD_IS_NULL = "The required field {} was left blank in the {} form"
UNABLE_TO_CREATE_RECORD = "Unable to create record. Message: {}"
UNABLE_TO_UPDATE_RECORD = "Unable to update record {}. Message: {}"

# Other
STATE_TO_PIPELINE = {
    'Sourced (no BMNT)': 'Source',
    '10% Curated (BMNT tool)': 'Curate',
    '20%-40% Curated (BMNT tool, little help)': 'Discover',
    '40%-80% Curated (Curation call)': 'Incubate',
    '100% Curated (Discovery Workshop)': 'Transition'
}