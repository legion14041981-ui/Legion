#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Legion AI System v2.0 - Setup Script
"""

import os
from setuptools import setup, find_packages

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='legion-ai',
    version='2.0.0',
    description='Мультиагентный AI-фреймворк с браузерной автоматизацией и Model Context Protocol',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Legion Team',
    author_email='legion14041981@gmail.com',
    url='https://github.com/legion14041981-ui/Legion',
    project_urls={
        'Documentation': 'https://www.notion.so/2ac65511388d815fa690c20766ed1206',
        'Source': 'https://github.com/legion14041981-ui/Legion',
        'Tracker': 'https://github.com/legion14041981-ui/Legion/issues',
    },
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>=3.9',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'pytest-playwright>=0.4.0',
            'black>=23.0.0',
            'pylint>=3.0.0',
            'mypy>=1.7.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.3.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'legion=src.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Framework :: AsyncIO',
    ],
    keywords='ai multi-agent automation mcp playwright orchestration',
    license='MIT',
)