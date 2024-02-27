#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

import os
import subprocess
import pathlib

copyright = '2024, UCD / iCRAG'
version = '0.2.6 Beta'
project = 'EGMS-toolkit'
author = 'Alexis Hrysiewicz University College Dublin / iCRAG'

extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.intersphinx",
    "pydoctor.sphinx_ext.build_apidocs",
    "sphinxcontrib.spelling",
    "sphinxarg.ext",
    "nbsphinx",
    "myst_parser",
    "sphinx_tabs.tabs",
]

nbsphinx_allow_errors = True
nbsphinx_execute = 'never'

templates_path = ['_templates']

exclude_patterns = []

rst_epilog = """
.. include:: <isonum.txt>
"""

spelling_word_list_filename = 'spelling_wordlist.txt'
html_theme = "sphinx_rtd_theme"
html_static_path = []

_git_reference = subprocess.getoutput('git rev-parse --abbrev-ref HEAD')
if _git_reference == 'HEAD':
    _git_reference = subprocess.getoutput('git rev-parse HEAD')

if os.environ.get('READTHEDOCS', '') == 'True':
    rtd_version = os.environ.get('READTHEDOCS_VERSION', '')
    if '.' in rtd_version:
        _git_reference = rtd_version

_EGMStoolkit_root = pathlib.Path(__file__).parent.parent.parent
_common_args = [
    f'--html-viewsource-base=https://github.com/alexisInSAR/EGMStoolkit.git/tree/{_git_reference}',
    f'--project-base-dir={_EGMStoolkit_root}', 
    f'--config={_EGMStoolkit_root}/setup.cfg',
]
pydoctor_args = {
    'main': [
        '--html-output={outdir}/api/', 
        '--project-name=EGMS-toolkit',
        f'--project-version={version}',
        '--docformat=google', 
        '--intersphinx=https://docs.python.org/3/objects.inv',
        '--theme=readthedocs',
        '--project-url=../index.html',
        f'{_EGMStoolkit_root}/src/EGMStoolkit',
        ] + _common_args,
    }

pydoctor_url_path = {
    'main': '/en/{rtd_version}/api',
    }