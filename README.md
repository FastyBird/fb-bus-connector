# FastyBird IoT FB BUS connector

[![Build Status](https://badgen.net/github/checks/FastyBird/fb-bus-connector/master?cache=300&style=flat-square)](https://github.com/FastyBird/fb-bus-connector/actions)
[![Licence](https://badgen.net/github/license/FastyBird/fb-bus-connector?cache=300&style=flat-square)](https://github.com/FastyBird/fb-bus-connector/blob/master/LICENSE.md)
[![Code coverage](https://badgen.net/coveralls/c/github/FastyBird/fb-bus-connector?cache=300&style=flat-square)](https://coveralls.io/r/FastyBird/fb-bus-connector)

![PHP](https://badgen.net/packagist/php/FastyBird/fb-bus-connector?cache=300&style=flat-square)
[![PHP latest stable](https://badgen.net/packagist/v/FastyBird/fb-bus-connector/latest?cache=300&style=flat-square)](https://packagist.org/packages/FastyBird/fb-bus-connector)
[![PHP downloads total](https://badgen.net/packagist/dt/FastyBird/fb-bus-connector?cache=300&style=flat-square)](https://packagist.org/packages/FastyBird/fb-bus-connector)
[![PHPStan](https://img.shields.io/badge/phpstan-enabled-brightgreen.svg?style=flat-square)](https://github.com/phpstan/phpstan)

![Python](https://badgen.net/pypi/python/fastybird-fb-bus-connector?cache=300&style=flat-square)
[![Python latest stable](https://badgen.net/pypi/v/fastybird-fb-bus-connector?cache=300&style=flat-square)](https://pypi.org/project/fastybird-fb-bus-connector/)
[![Python downloads month](https://img.shields.io/pypi/dm/fastybird-fb-bus-connector?cache=300&style=flat-square)](https://pypi.org/project/fastybird-fb-bus-connector/)
[![Black](https://img.shields.io/badge/black-enabled-brightgreen.svg?style=flat-square)](https://github.com/psf/black)
[![MyPy](https://img.shields.io/badge/mypy-enabled-brightgreen.svg?style=flat-square)](http://mypy-lang.org)

## What is FastyBird IoT FB BUS connector?

FB BUS connector is a combined [FastyBird](https://www.fastybird.com) [IoT](https://en.wikipedia.org/wiki/Internet_of_things) extension which is integrating [FIB](https://www.fastybird.com) aka **F**astyBird **I**nterface **B**us for connected devices

[FastyBird](https://www.fastybird.com) [IoT](https://en.wikipedia.org/wiki/Internet_of_things) FB BUS connector is
an [Apache2 licensed](http://www.apache.org/licenses/LICENSE-2.0) distributed extension, developed
in [PHP](https://www.php.net) with [Nette framework](https://nette.org) and in [Python](https://python.org).

### Features:

- FIB v1 protocol devices support
- FIB connector management for [FastyBird](https://www.fastybird.com) [IoT](https://en.wikipedia.org/wiki/Internet_of_things) [devices module](https://github.com/FastyBird/devices-module)
- FIB device management for [FastyBird](https://www.fastybird.com) [IoT](https://en.wikipedia.org/wiki/Internet_of_things) [devices module](https://github.com/FastyBird/devices-module)
- [{JSON:API}](https://jsonapi.org/) schemas for full api access
- Integrated connector Python worker

## Requirements

PHP part of [FastyBird](https://www.fastybird.com) FB BUS connector is tested against PHP 7.4
and [ReactPHP http](https://github.com/reactphp/http) 0.8 event-driven, streaming plaintext HTTP server
and [Nette framework](https://nette.org/en/) 3.0 PHP framework for real programmers

Python part of [FastyBird](https://www.fastybird.com) FB BUS connector is tested against [Python 3.7](http://python.org)

## Installation

### Manual installation

#### Application backend in PHP

The best way to install **fastybird/fb-bus-connector** is using [Composer](http://getcomposer.org/):

```sh
composer require fastybird/fb-bus-connector
```

#### Application workers in Python

The best way to install **fastybird-fb-bus-connector** is using [Pip](https://pip.pypa.io/en/stable/):

```sh
pip install fastybird-fb-bus-connector
```

### Marketplace installation

You could install this connector in your [FastyBird](https://www.fastybird.com) [IoT](https://en.wikipedia.org/wiki/Internet_of_things) application under marketplace section

## Documentation

Learn how to connect devices with FIB interface to FastyBird IoT system
in [documentation](https://github.com/FastyBird/fb-bus-connector/blob/master/.docs/en/index.md).

## Feedback

Use the [issue tracker](https://github.com/FastyBird/fb-bus-connector/issues) for bugs
or [mail](mailto:code@fastybird.com) or [Tweet](https://twitter.com/fastybird) us for any idea that can improve the
project.

Thank you for testing, reporting and contributing.

## Changelog

For release info check [release page](https://github.com/FastyBird/fb-bus-connector/releases)

## Maintainers

<table>
	<tbody>
		<tr>
			<td align="center">
				<a href="https://github.com/akadlec">
					<img width="80" height="80" src="https://avatars3.githubusercontent.com/u/1866672?s=460&amp;v=4">
				</a>
				<br>
				<a href="https://github.com/akadlec">Adam Kadlec</a>
			</td>
		</tr>
	</tbody>
</table>

***
Homepage [https://www.fastybird.com](https://www.fastybird.com) and
repository [https://github.com/fastybird/fb-bus-connector](https://github.com/fastybird/fb-bus-connector).
