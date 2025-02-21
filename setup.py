#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='openwisp-sentry-utils',
    version='0.1.0',
    license='MIT',
    author='Gagan Deep',
    author_email='support@openwisp.io',
    description='OpenWISP Sentry Utility Module',
    long_description=open('README.rst').read(),
    url='http://openwisp.org',
    download_url='https://github.com/openwisp/openwisp-sentry-utils/releases',
    platforms=['Platform Independent'],
    keywords=['sentry', 'python'],
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'sentry-sdk~=1.5.12',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: System :: Networking',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GPL v3',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ],
)
