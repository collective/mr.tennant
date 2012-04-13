from os.path import abspath, dirname, join
try:
  # try to use setuptools
  from setuptools import setup
  setupArgs = dict(
      include_package_data=True,
      namespace_packages=['dm'],
      zip_safe=True,
      )
except ImportError:
  # use distutils
  from distutils import setup
  setupArgs = dict(
    )

cd = abspath(dirname(__file__))
pd = join(cd, 'dm', 'historical')

def pread(filename, base=pd): return open(join(base, filename)).read().rstrip()

setup(name='dm.historical',
      version=pread('VERSION.txt').split('\n')[0].rstrip(),
      description='Historical state of objects stored in the ZODB',
      long_description=pread('README.txt'),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: ZODB',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Utilities',
        ],
      author='Dieter Maurer',
      author_email='dieter@handshake.de',
      packages=['dm', 'dm.historical',],
      keywords='historical state ZODB analysis recovery ',
      license='BSD (see "dm/historical/LICENSE.txt", for details)',
      **setupArgs
      )
