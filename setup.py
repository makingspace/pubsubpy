from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import sys

from setuptools import find_packages, setup

if not os.getenv('JENKINS_URL'):
    with open(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                'README.md')) as readme:
        README = readme.read()
else:
    README = ''

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup_requires = ['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(
    sys.argv) else []

setup(
    name='pubsubpy',
    version='2.3.0',
    packages=find_packages(),
    install_requires=[
        'future',
        'kombu',
    ],
    setup_requires=setup_requires,
    tests_require=[
        'mock',
        'pytest',
    ],
    include_package_data=True,
    license='MIT',
    description=('Client library for an AMQP-based pubsub.'),
    long_description=README,
    url='https://github.com/makingspace/pubsubpy',
    author='John Sloboda',
    author_email='sloboda@makespace.com',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ],
)
