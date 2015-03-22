#!/usr/bin/env python

from distutils.core import setup

setup(
    name            = 'equivalence',
    version         = '0.2',
    py_modules      = ['equivalence'],
    author          = 'George Sakkis',
    author_email    = 'george.sakkis@gmail.com',
    url             = 'http://code.google.com/p/pyquivalence/',
    description     = 'Equivalence relations',
    long_description=
'''*equivalence* is a Python module for building equivalence relations,
partitionings of objects into sets that maintain the equivalence relation
properties (reflexivity, symmetry, transitivity). Two objects are considered
equivalent either explicitly, after being merged, or implicitly, through a key
function.''',
    classifiers     = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
