#/usr/bin/env python3

import os
from setuptools import setup

setup(
    name='cue2flac',
    version='1.0',
    description='A script splitting a FLAC image into tracks based on a .cue file.',
    author='yakcyll~',
    python_requires=">=3.3",
    packages=['cue2flac'],
    package_dir={'cue2flac': 'src'},
    entry_points={
        'console_scripts': [
            'cue2flac = cue2flac.cue2flac:main',
        ],
    },
)
