Canvas LMS API Client Library
=============================

[Overview](#overview)  
[Testing](#testing)  
[Documentation](#documentation)  
[Installation](#installation)  
[Usage](#usage)  
[Contributing](#contributing)  
[References](#references)  

Overview
--------

This is a library for making requests to a Canvas LMS API.

Testing
-------

This project is tested with [tox](https://tox.readthedocs.io/en/latest/).

Run the tox command to run checks and unit tests:
```
$ tox
```

By default, this project's tox runs:

 * [flake8](http://flake8.pycqa.org/en/latest/)
 * [mypy](https://github.com/python/mypy)
 * [pytest](https://docs.pytest.org/en/latest/)

To create test coverage reports:
```
$ tox -e cov
```

Deployment
----------

Deployment to pypi is done with tox:
```
$ tox -e deploy
```
Make sure to bump the version in setup.py before deploying.

Documentation
-------------

This project has Sphinx documentation at the following url:  
https://wgwz.github.io/canvas-lms-tools/

The public Canvas LMS API documentation is also very useful:  
https://canvas.instructure.com/doc/api/index.html

Installation
------------

To install, use pip:

    pip install canvas_api_client

Or clone the repo:

    git clone https://github.com/lcary/canvas-lms-tools.git
    cd canvas-lms-tools/canvas_api_client
    python setup.py install

Usage
-----

Adding the client as a dependency in your project's `requirements.txt`
file is the intended way to use the client.

#### REPL Example

```
$ python
>>> from canvas_api_client.v1_client import CanvasAPIv1
>>> url = 'https://my.canvas.instance.com/api/v1/'
>>> token = '1396~xxxxxxxxxxxxxxxxxxxTHISxISxNOTxAxREALxTOKENxxxxxxxxxxxxxxxxxxxxx'
>>> api = CanvasAPIv1(url, token)
>>> l = api.get_account_blueprint_courses('1234')
>>> for r in l.json():
...     print(r['id'], r['name'])
...
49400 Course_9000_Blueprint
57600 Spring_2018_Blueprint
```

#### Script Example

This very simple example requires a few environment variables. The
API URL and token should be something like:
```
CANVAS_API_URL=https://my.canvas.instance.com/api/v1/
CANVAS_API_TOKEN=1396~xxxxxxxxxxxxxxxxxxxTHISxISxNOTxAxREALxTOKENxxxxxxxxxxxxxxxxxxxxx
```

The recommended approach is to use a config file with limited read
permissions instead of environment variables, but bear with me here.

Once installed in your project via pip, use as follows:

```python
from os import environ
from pprint import pprint

from canvas_api_client.v1_client import CanvasAPIv1 

url = environ.get('CANVAS_API_URL')
token = environ.get('CANVAS_API_TOKEN')

api = CanvasAPIv1(url, token)
params = {"override_sis_stickiness": "true"}
response = api.import_sis_data('1', './courses.csv', params=params)

print('SIS Import Response:')
pprint(response.json())
```

#### CanvasAPIv1

This library is meant to be imported into your code. The `CanvasAPIv1` client
object requires a `api_url` argument and a `api_token` argument. The `api_url`
should likely be defined in a configuration file, and should be the full API
URL without the endpoint, e.g. `https://canvas.com/api/v1/`. The `api_token`
should similarly be defined in a config file, and is the token generated in
the Canvas settings page.

The `CanvasAPIv1` client object can also be called with any of the
following optional requirements.  They can be overridden by arguments
to the individual methods.

* *per_page*: passed to the Canvas API in requests that receive
   paginated responses.  Sets the page size; the default is 100, the
   largest size respected by the Canvas API.

* *flatten_response*: If the Canvas API returns a paginated response,
   return the results as a simple list.

* *is_sis_course_id*: Prepend 'sis_course_id' to the course ID
   argument when passing it to the Canvas API.  This allows you to use
   your SIS course IDs instead of Canvas serial numbers.

* *is_sis_account_id*: Prepend 'sis_account_id' to the account ID
   argument when passing it to the Canvas API.  This allows you to use
   your SIS account IDs instead of Canvas serial numbers.

There are a few helper functions that assist in sharing code between methods
in `CanvasAPIv1` which are worth pointing out. For example, there is a method
for each request type, such as `._get()` for GET requests, etc. Each one of
these request type methods invokes `self._send_request()` which takes a
number of parameters and returns a
[`requests.Response`](http://docs.python-requests.org/en/master/api/#requests.Response)
object by default. Most of the public methods of the api client thus return
a `Response` object, so the caller will have access to the typical response
methods, such as `response.json()`.

I say "by default", because it is possible to pass in your own requests
library. This is not necessarily recommended; this capability only exists for
the sake of easy dependency injection in unit testing as well as compatibility
with libraries such as requests-oauthlib.

Refer to the client interface [documentation](#documentation) for more information.

Contributing
------------

#### Building Wheels

Building the wheel:

    python setup.py bdist_wheel

#### Installing Wheels

How to install the client for testing:

    pip uninstall canvas_api_client || echo "Already uninstalled."
    pip install --no-index --find-links=dist canvas_api_client

Alternatively, install by specifying the full or relative path to the `.whl` file:

    pip install --no-index /path/to/canvas-lms-tools/canvas_api_client/dist/canvas_api_client-<version>-py2.py3-none-any.whl

(You may need to `pip install wheel` first if you are installing from another 
project. Consult [stack overflow](https://stackoverflow.com/questions/28002897/wheel-file-installation)
for more help.)

#### Sphinx Docs

Creating the docs:

    cd docs
    pip install -r requirements.txt
    pip install canvas_api_client
    make html
    open build/html/index.html

Deploying the docs to GitHub pages:

    git checkout master
    git pull
    git branch -D gh-pages
    git checkout -b gh-pages
    rm -rf ./*
    touch .nojekyll
    git checkout master canvas_api_client/docs/
    < build the docs as above > 
    mv canvas_api_client/docs/build/html/* ./
    rm -rf canvas_api_client
    git add -A
    git commit
    git push -f origin gh-pages

For more info see the [GitHub Pages documentation](https://pages.github.com/),
the [Sphinx docs](http://www.sphinx-doc.org/en/master/contents.html),
or the following [script docs](http://www.willmcginnis.com/2016/02/29/automating-documentation-workflow-with-sphinx-and-github-pages/).

References
----------

This project was originally created with the following "cookiecutter" tool:  
https://github.com/wdm0006/cookiecutter-pipproject
