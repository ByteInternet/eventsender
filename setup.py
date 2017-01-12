from setuptools import setup, find_packages

setup(
    name='eventsender',
    version='1.0',
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
    ],
    keywords='amqp rabbitmq events eventsender',
    description='RabbitMQ event sender',
    install_requires=['pika==0.10.0'],
)
