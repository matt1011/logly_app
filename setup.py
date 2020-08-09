from setuptools import setup, find_packages

import os

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="logly",
    version="0.0.1",
    author='Matt Eisner',
    description='A log analysis web app.',
    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests", 'examples'
    ]),
    install_requires=required,
    tests_require=[
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'numpy'
    ],

)
