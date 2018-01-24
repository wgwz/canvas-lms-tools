Canvas LMS API Client Library
=============================

version number: 0.0.1
author: Luc Cary

Overview
--------

This is a library for making requests to a Canvas LMS API.

Canvas LMS API documentation:
https://canvas.instructure.com/doc/api/index.html

This project was originally created with the following "cookiecutter" tool:
https://github.com/wdm0006/cookiecutter-pipproject

Installation / Usage
--------------------

To install use pip:

    $ pip install canvas_api_client


Or clone the repo:

    $ git clone https://github.com/lcary/canvas_api_client.git
    $ python setup.py install
    
Contributing
------------

This project is tested with python3, and additionally has mypy integration.

How to install the client for testing:

    pip uninstall canvas_api_client || echo "Already uninstalled."
    python setup.py bdist_wheel
    pip install --no-index --find-links=dist canvas_api_client

Example
-------

Once installed in your project via pip, use as follows:

```python
import os

from canvas_api_client.v1_client import CanvasAPIv1

url = os.environ('CANVAS_API_URL')
token = os.environ('CANVAS_API_TOKEN')
api = CanvasAPIv1(url, token)

course_id = '<sis_course_id>'
params = {
    "per_page": "100",
    "include[]": "enrollments",
    "include_inactive": "true""}
course_users = []
for user_data_list in api.get_course_users(course_id, params=params):
    course_users.extend(user_data_list)
```
