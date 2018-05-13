from typing import List, NamedTuple

# Convert NamedTuples to PEP-0526 syntax when python3.6 is available
# on the CUIT servers. Until then, we have to use the python3.5 syntax.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple

Term = NamedTuple(
    'Term',
    [
        ('year', int),
        ('semester', int),
        ('term_id', int),
    ]
)  # yapf: disable

TermList = List[Term]
