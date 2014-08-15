check_debian_repository
=======================

Check Debian Repository for consistency, download all missing files

Requirements
============

* python-multiprocessing
* python-magic
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

