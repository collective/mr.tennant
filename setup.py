# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.0a1'

setup(name='mr.tennant',
      version=version,
      description="A git remote ZServer type. Yeah. Seriously. It lets you pull TTW code.",
      long_description=read('README'),
      classifiers=[
        "Framework :: ZODB",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Topic :: Software Development :: Version Control",
        ],
      keywords='git zope crazy',
      author='Matthew Wilkes',
      author_email='matthew@matthewwilkes.co.uk',
      url='https://github.com/collective/mr.tennant',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir = {'':'src'},
      namespace_packages=['mr'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'plone.app.testing',
                        'dm.historical',
                        ],
      entry_points="""
      """,
      )
