import os
import tarfile
import base64
import json
from time import sleep
from subprocess import call
from paver.easy import *
from paver.setuputils import setup, find_packages

try:
    from http import client as http
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
    import httplib as http

setup(
    name='neo4jdb',
    version='0.0.8',
    author='Jacob Hansson',
    author_email='jakewins@gmail.com',
    packages=find_packages(),
    py_modules=['setup'],
    include_package_data=True,
    install_requires=[],
    url='https://github.com/jakewins/neo4jdb-python',
    description='DB API 2.0 driver for the Neo4j graph database.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)

BUILD_DIR = 'build'
NEO4J_VERSION = '2.3.1'
DEFAULT_USERNAME = u'neo4j'
DEFAULT_PASSWORD = u'neo4j'

@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass


@task
def start_server():
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    if not path(BUILD_DIR + '/neo4j.tar.gz').access(os.R_OK):
        print("Downloading Neo4j Server")
        urlretrieve("http://dist.neo4j.org/neo4j-community-%s-unix.tar.gz" % NEO4J_VERSION, BUILD_DIR + "/neo4j.tar.gz")

    if not path(BUILD_DIR + '/neo4j').access(os.R_OK):
        print("Unzipping Neo4j Server..")
        call(['tar','-xf', BUILD_DIR + "/neo4j.tar.gz", '-C', BUILD_DIR])
        os.rename(BUILD_DIR + "/neo4j-community-%s" % NEO4J_VERSION, BUILD_DIR + "/neo4j")

    call([BUILD_DIR + "/neo4j/bin/neo4j", "start"])
    change_password()


@task
def stop_server():
    if path(BUILD_DIR + '/neo4j').access(os.R_OK):
        call([BUILD_DIR + "/neo4j/bin/neo4j", "stop"])


@task
def change_password():
    """
    Changes the standard password from neo4j to testing to be able to run the test suite.
    """
    auth = base64.encodestring(DEFAULT_USERNAME + ":" + DEFAULT_PASSWORD).strip()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Basic %s" % auth
    }
    response = None
    retry = 0
    while not response:  # Retry if the server is not ready yet
        sleep(1)
        try:
            con = http.HTTPConnection('localhost:7474', timeout=10)
            con.request('GET', 'http://localhost:7474/user/neo4j', headers=headers)
            response = json.loads(con.getresponse().read().decode('utf-8'))
        except ValueError:
            pass
        retry += 1
        if retry > 10:
            print("Could not change password for user neo4j")
            break
    if response and response.get('password_change_required', None):
        payload = json.dumps({'password': 'testing'})
        con.request('POST', 'http://localhost:7474/user/neo4j/password', payload, headers)
    con.close()

