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

To install, use pip:

    $ pip install canvas_api_client

Or clone the repo:

    $ git clone https://github.com/lcary/canvas_api_client.git
    $ python setup.py install

Adding the client as a dependency in your project's `requirements.txt`
file is the intended way to use the client.

#### Using CanvasAPIv1 ####

This library is meant to be imported into your code. The `CanvasAPIv1` client
object requires a `api_url` argument and a `api_token` argument. The `api_url`
should likely be defined in a configuration file, and should be the full API
URL without the endpoint, e.g. `https://canvas.com/api/v1/`. The `api_token`
should similarly be defined in a config file, and is the token generated in
the Canvas settings page.

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

See the examples section at the bottom for more info.

Contributing
------------

This project is tested with python3, and additionally has mypy integration.

Note: before building, make sure to bump the `__version__` in the `setup.py` file.

#### Building Wheels ####

Building the wheel:

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

Refer to the client interface documentation for more information.
