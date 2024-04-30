#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""EGMS-toolkit setuptools configuration

"""

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open("README.rst", "r") as readme_file:
    readme = readme_file.read()

setup(name='EGMStoolkit', 
    version='0.2.10', 
    author="Alexis Hrysiewicz UCD/iCRAG",
    author_email="alexis.hrysiewicz@ucd.ie",
    description="EGMS Toolbox",
    long_description=readme,
    long_description_content_type="text/rst",
    url="https://github.com/alexisInSAR/EGMStoolkit.git",
    packages=find_packages('EGMStoolkit'),
    package_dir = {"": "src"},
        python_requires='>=3.8',
    install_requires= required,
    license='GNU',
    license_files=('LICENSE'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Earth Sciences",
    ],
    entry_points={
        'console_scripts': ['EGMStoolkit=EGMStoolkit.EGMStoolkitapp:main']},
    )