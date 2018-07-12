from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.0.1-alpha'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_requirements = f.read().split('\n')
    
setup(
    name='bowker_api_client',
    version=__version__,
    description='This is an api client for the bowker isbn rest api',
    long_description=long_description,
    url='https://github.com/wgwz/canvas-lms-tools',
    download_url='https://github.com/wgwz/canvas-lms-tools/archive/' +
    __version__,
    license='Apache',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author='Thomas Barraro',
    install_requires=all_requirements,
    dependency_links=all_requirements,
    author_email='tb2766@columbia.edu'
)
