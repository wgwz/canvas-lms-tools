from typing import NamedTuple

# Convert NamedTuples to PEP-0526 syntax when python3.6 is available
# on the cuit servers. Until then, we have to use the python3.5 syntax.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple

Course = NamedTuple(
    'Course',
    [
        ('subject_code', str),
        ('subject_name', str),
        ('subject_long_name', str),
        ('course_number', str),
        ('suffix_name', str),
        ('section', str),
        ('ucid', str),  # universal course identifier
        ('course_title', str),
        ('bulletin_code_1', str),  # separates subject and course number
        ('bulletin_code_2', str)
    ])  # when 2 digits, overrides bulletin_code_1
