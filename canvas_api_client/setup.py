from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.0.1'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_requirements = f.read().split('\n')

setup(
    name='canvas_api_client',
    version=__version__,
    description='This is a library for making requests to a Canvas LMS API.',
    long_description=long_description,
    url='https://github.com/lcary/canvas_api_client',
    download_url='https://github.com/lcary/canvas_api_client/archive/' + __version__,
    license='BSD',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author='Luc Cary',
    install_requires=all_requirements,
    dependency_links=all_requirements,
    author_email='luc.cary@gmail.com'
)
