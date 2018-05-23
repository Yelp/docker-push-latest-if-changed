from setuptools import setup

setup(
    name='docker-push-latest-if-changed',
    description='Only push newly tagged docker images if the images changes.',
    url='https://github.com/Yelp/docker-push-latest-if-changed',
    version='0.0.0',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    py_modules=['docker_push_latest_if_changed'],
    install_requires=[
        'docker-py >= 1.2.3, < 2'
    ],
    entry_points={'console_scripts': [
        'docker-push-latest-if-changed = docker_push_latest_if_changed:main',
    ]},
)
