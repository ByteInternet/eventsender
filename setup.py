#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import abspath, dirname, join


def readfile(filename):
    path = join(dirname(abspath(__file__)), filename)
    with open(path, 'rt') as filehandle:
        return filehandle.read()


setup(
    name='eventsender',
    version='1.1.2',
    packages=find_packages(exclude=['tests*']),
    url='https://github.com/ByteInternet/eventsender',
    author='Byte B.V.',
    author_email='tech@byte.nl',
    license='MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Topic :: Communications',
        'Topic :: Internet',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='amqp rabbitmq events eventsender',
    description='RabbitMQ event sender',
    long_description=readfile('README.rst'),
    long_description_content_type='text/x-rst',
    install_requires=['pika==1.1.1'],
)
