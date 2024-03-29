# -*- coding: utf-8 -*-

#     Copyright 2021. FastyBird s.r.o.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

# Library dependencies
import codecs
import re
from Cython.Distutils import build_ext
from setuptools import Extension, setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def read(*parts):
    filename = path.join(path.dirname(__file__), *parts)

    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)

    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


VERSION: str = find_version("fastybird_fb_bus_connector", "__init__.py")

strategies = []

for s in ['TSA']:
    strategies.extend([
        '-DPJON_INCLUDE_{}'.format(s),
        '-D{}_RESPONSE_TIME_OUT=100000'.format(s)
    ])

setup(
    version=VERSION,
    name="fastybird-fb-bus-connector",
    author="FastyBird",
    author_email="code@fastybird.com",
    license="Apache Software License (Apache Software License 2.0)",
    description="FastyBird IoT connector for FB BUS devices",
    url="https://github.com/FastyBird/fb-bus-connector",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    packages=find_packages(),
    package_data={"fastybird_fb_bus_connector": ["py.typed"]},
    install_requires=[
        "Cython",
        "fastnumbers",
        "fastybird-devices-module",
        "fastybird-metadata",
        "inflection",
        "kink",
        "libscrc==1.7.1",
        "nose",
        "setuptools",
        "whistle"
    ],
    download_url="https://github.com/FastyBird/fb-bus-connector/archive/%s.tar.gz" % VERSION,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: PHP",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications",
        "Topic :: Home Automation",
        "Topic :: System :: Hardware",
    ],
    cmdclass={"build_ext": build_ext},
    ext_modules=[
        Extension(
            "fastybird_fb_bus_connector.pjon._pjon",
            sources=["fastybird_fb_bus_connector/pjon/_pjon.pyx"],
            language="c++",
            extra_compile_args=strategies + [
                '-std=c++11',
                '-DPJON_INCLUDE_ANY',
                '-DPJON_INCLUDE_PACKET_ID=true',
                '-DPJON_INCLUDE_ASYNC_ACK=true',
                '-DPJON_MAX_PACKETS=100',
                '-DPJON_PACKET_MAX_LENGTH=1536',
                '-DLINUX',
                '-Wno-unneeded-internal-declaration',
                '-Wno-logical-op-parentheses',
                '-Wno-unused-variable'],
            include_dirs=['PJON/src'],
            compiler_directives={
                'binding': True,
                'embedsignature': True
            }
        )
    ])
