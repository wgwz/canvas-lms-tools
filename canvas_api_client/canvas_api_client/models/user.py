from typing import NamedTuple

# Convert NamedTuples to PEP-0526 syntax when python3.6 is available
# on the CUIT servers. Until then, we have to use the python3.5 syntax.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple

User = NamedTuple(
    'User',
    [
        ('user_id', str),
        ('login_id', str),
        ('password', str),
        ('first_name', str),
        ('last_name', str),
        ('short_name', str),
        ('email', str),
        ('status', str),
    ]
)  # yapf: disable
