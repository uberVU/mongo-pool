from setuptools import setup
import io
import os

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')

setup(
    name='mongo-pool',
    version='0.5.0',
    url='http://github.com/ubervu/mongo-pool/',
    description='The tool that keeps all your mongos in one place',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache Software License',
    author='UberVU',
    author_email="development@ubervu.com",
    install_requires=['pymongo>=3.6.1', 'six>=1.15.0'],
    packages=['mongo_pool'],
    include_package_data=True,
    platforms='any',
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    extras_require={
        'testing': ['nose', 'mock'],
    }
)
