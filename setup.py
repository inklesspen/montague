# -*- encoding: utf-8 -*-
import glob
import io
import re
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ).read()

setup(
    name="montague",
    version="0.2.0",
    license="MIT",
    description=("Montague provides functions to load WSGI apps and servers "
                 "based on configuration files. "
                 "It's based on PasteDeploy's INI file support."),
    long_description="%s\n%s" % (read("README.rst"),
                                 re.sub(":obj:`~?(.*?)`",
                                        r"``\1``", read("CHANGELOG.rst"))),
    author="Jon Rosebaugh",
    author_email="jon@inklesspen.com",
    url="https://github.com/inklesspen/montague",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(i))[0] for i in glob.glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Utilities",
    ],
    keywords=[
        # eg: "keyword1", "keyword2", "keyword3",
    ],
    install_requires=[
        # eg: "aspectlib==1.1.1", "six>=1.7",
        "six>=1.8.0",
        "zope.interface>=4.1.1",
        "characteristic>=14.2.0",
    ],
    extras_require={
        # eg: 'rst': ["docutils>=0.11"],
    },
    entry_points={
        "console_scripts": [
            "montague = montague.__main__:main"
        ]
    }

)
