Canvas LMS API Client Library
=============================

version number: 0.2.0
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

Note: before building, make sure to bump the `__version__` in the `setup.py` file.

#### Building Wheels ####

Building the wheel:

    pip install -r requirements.txt
    python setup.py bdist_wheel

#### Installing Wheels ####

How to install the client for testing:

    pip uninstall canvas_api_client || echo "Already uninstalled."
    pip install --no-index --find-links=dist canvas_api_client

Alternatively, install by specifying the full or relative path to the `.whl` file:

    pip install --no-index /path/to/canvas-lms-tools/canvas_api_client/dist/canvas_api_client-<version>-py2.py3-none-any.whl

(You may need to `pip install wheel` first if you are installing from another 
project. Consult [stack overflow](https://stackoverflow.com/questions/28002897/wheel-file-installation)
for more help.)

#### Deploying Wheels ####

Publishing to pypi (requires [twine](https://packaging.python.org/tutorials/distributing-packages/#requirements-for-packaging-and-distributing) to be installed):

    twine upload dist/canvas_api_client-<version>-py2.py3-none-any.whl

#### Building Docs ####

Creating the docs:

    cd docs
    pip install -r requirements.txt
    make html
    open build/html/index.html

Example
-------

Once installed in your project via pip, use as follows:

```python
import os

from canvas_api_client.v1_client import CanvasAPIv1

url = os.environ.get('CANVAS_API_URL')
token = os.environ.get('CANVAS_API_TOKEN')
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
