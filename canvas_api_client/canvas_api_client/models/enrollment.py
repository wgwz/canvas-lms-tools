from typing import Dict, NamedTuple

# Convert NamedTuples to PEP-0526 syntax when python3.6 is available
# on the CUIT servers. Until then, we have to use the python3.5 syntax.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple

# Tuple for storing CSV line info of enrollments.csv
Enrollment = NamedTuple(
    'Enrollment',
    [
        ('course_id', str),
        ('user_id', str),
        ('role_id', str),
        ('section_id', str),
        ('status', str)
    ]
)  # yapf: disable

EnrollmentDict = Dict[str, Enrollment]
