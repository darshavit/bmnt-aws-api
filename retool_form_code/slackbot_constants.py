FIELD_NAMES_TO_SEARCH = [
    'problem_title',
    'problem_statement',
    'sponsor_name',
    'sponsor_title',
    'sponsor_email',
    'sponsor_division'
    'background',
    'elements',
    'roles',
    'processes',
    'data',
    'employee_sourced_curated',
    'program',
    'setting'
]

FIELD_NAMES_TO_SEARCH_STRING = ', '.join(FIELD_NAMES_TO_SEARCH)

GREETING_WORDS = [
    'hello',
    'hi',
    'hey',
    'howdy',
    'sup'
]

RECORDS_TO_DISPLAY = 5

HELP_TEXT = 'Hi there, I am the problem data bot :robot_face:. I can be used to search BMNTs estensive database of ' \
            'problems that helps you find similar problems based on your request!\nPlease add me <@UK7MNRJTX>. Say ' \
            'Hello!\nGo to my direct message and simply enter */data* followed by search terms separated by commas.' \
            '\nExample --> "/data Analysis, UAV, Systems Development"'

MORE_HELP_TEXT = '1. Add me to your slack account through the direct message section <@UK7MNRJTX>.\n2. Start by ' \
                 'saying Hello! To search, enter */data*\n3. Provide some *search terms*. As an example lets say I ' \
                 'wanted to see all problems that contain data of "Classified Data" and a process of "Analysis". ' \
                 'Type "*/data Classified Data, Analysis"*. Thats it!\n4. Ill query our database for matching records, '\
                 'and present them to you when Im finished! Your text should be formatted such that *distinct phrases' \
                 '/labels are separated by commas.* You do not need to specify which fields to search in. I will '\
                 '*automatically search each of the provided phrases/labels across the fields in airtable.*\n' \
                 '5. In the future, I hope to be able to help you with more!'


