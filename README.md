check_debian_repository
=======================

Check Debian Repository for consistency, download all missing files

About
=====

Its purpose is to check the integrity of a Debian GNU repository evaluating each section and architecture in a Packages.bz2 file.
Check integrity, checksum and mime of every file in repository, also uses python-multiprocessing to simultaneously download all missing files.

Requirements
============
* python-multiprocessing
* python-requests

Usage
=====

  check_mirror.py -s SUITE -a ARCH -d /repository/dir


where:
 SUITE = Debian suite (ex: wheezy, jessie, wheezy-backports)

 ARCH = Architecture (ex: amd64, armel, mipsel, armhf, etc)

example:
-- check for a wheezy-backports repository, architecture amd64 found in directory "/opt/repo/mirrors/debian"

check_mirror.py -s wheezy-backports -a amd64 -d /opt/repo/mirrors/debian

Copyright and license
=====================

Code and documentation copyright 2011-2014 Jesus Lara. Code released under the GPL v3 license. Docs released under Creative Commons.
