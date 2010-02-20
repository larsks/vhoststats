import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='vhoststats',
        version='20100218.1',
        description='Show Apache virtual host activity',
        long_description=read('README.rst'),
        author='Lars Kellogg-Stedman',
        author_email='lars@oddbit.com',
        packages=['vhoststats'],
        scripts=['scripts/vhoststats'],
        install_requires=['pqs'],
        )

