#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-usernamefield',
    description="Field to manage denormalisation of User.username in Django.",
    version='0.1',
    url='http://code.playfire.com/',

    author='Playfire.com',
    author_email='tech@playfire.com',
    license='BSD',

    packages=find_packages(),
)
