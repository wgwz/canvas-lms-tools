from typing import NamedTuple

# Convert NamedTuples to PEP-0526 syntax when python3.6 is available
# on the CUIT servers. Until then, we have to use the python3.5 syntax.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple

SubAccount = NamedTuple(
    'SubAccount',
    [
        ('sub_account_id', str),
        ('sub_account_is_per_subject', bool)  # previously named subject_on
    ]
)  # yapf: disable

Account = NamedTuple(
    'Account',
    [
        ('school_code', str),
        ('school_name', str),
        ('dept_code', str),
        ('dept_name', str),
        ('sub_account', SubAccount)
    ]
)  # yapf: disable
