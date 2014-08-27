#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
check_mirror

Check for Debian repository consistency
usage: check_mirror.py -s wheezy -a arch(ej: amd64) -d /path/to/repository
'''

import os
import sys, getopt
import bz2
import re
import mimetypes
import random
import hashlib
import requests
import signal
import multiprocessing
from multiprocessing import Pool

from check_config import config
configdata = config("checkrepo.conf")

datamirrors = configdata.ShowItemSection("mirrors")
mirrors = []
for i in range(len(datamirrors)):
	mirrors.append(datamirrors[i][1])

archs = configdata.ShowValueItem("repo","arch").split(",")
sections = configdata.ShowValueItem("repo","sections").split(",")
exclude_dbg = configdata.ShowValueItem("conf","exclude_dbg") == "True"
suites = configdata.ShowValueItem("repo","suites").split(",")
repo_path = ''

maxjobs = int(configdata.ShowValueItem("conf","maxjobs"))
jobs = []                   # current list of queued jobs
jobs_args = []
# Default wget options to use for downloading each URL
wget = "wget -nd -np -c -r "

#put all the available packages into this object
package_objects = {}

'''
Create a Debian Package definition
'''
class Deb:
	def __init__(self, path, package):
		self.package = package
		self.name = package.get_field("Package")
		mirror = random.choice(mirrors)
		self.uri = mirror+package.get_field("Filename")
		self.filename = os.path.join(path, package.get_field("Filename"))

	def get_download_uri(self):
		return self.uri

	def get_filename(self):
		return self.filename

	def md5sum(self, blocksize=65536):
		hash = hashlib.md5()
		with open(self.filename, "r+b") as f:
			for block in iter(lambda: f.read(blocksize), ""):
				hash.update(block)
		return hash.hexdigest()

	def verify_deb(self):
		d = os.path.dirname(self.filename)
		if not os.path.exists(d):
			# directory missing, create directory
			os.makedirs(d)
		if exclude_dbg:
			if "-dbg" in self.filename:
				# file is a dbg file
				return True
		if (not os.path.isfile(self.filename)):
			# file not exists
			print "verify_deb: filename %s is missing" % self.filename
			return False
		else:
			# file exists, verify mimetype and checksum
			mtype,entype = mimetypes.guess_type(self.filename)
			md5sum = self.package.get_field("MD5sum")
			if mtype == 'application/x-debian-package':
				# its a valid Debian package
				if not md5sum == self.md5sum():
					# a Debian package with failed md5sum
					print "verify_deb: md5sum failed for filename %s" % self.filename
					return False
				else:
					return True
			else:
				# its a Fake file
				print "verify_deb: mimetype failed, remove fake file %s" % self.filename
				os.remove(self.filename)
				return False

	def download(self):
		try:
			print "downloading %s from %s" % (self.filename, self.uri)
			r = requests.get(self.uri)
			if r.status_code == requests.codes.ok:
				print "--- content type is %s" % r.headers['content-type']
				if 'text/html' in r.headers['content-type']:
					return False
				else:
					try:
						print "uri: %s" % self.uri
						with open(self.filename, 'wb') as f:
							for chunk in r.iter_content(chunk_size=1024):
								if chunk: # filter out keep-alive new chunks
									f.write(chunk)
									f.flush()
						print "download of %s done" % self.filename
						return True
					except (KeyboardInterrupt, SystemExit):
						raise
		except IOError:
			print "Name or service not known"

'''
Parse a debian package description into a dictionary
'''
class Package:
    def __init__(self, p):
        self.fields = {}
        r = re.compile('(?P<field>^.*?): (?P<value>.*$)')
        for item in p:
			match = r.match(item)
			if match:
				self.fields[match.group("field")] = match.group("value")

    def get_field(self, field):
        return self.fields[field]

def parse_packages_file(fileh):
    try:
		package_lines = []
		for line in fileh.readlines():
			if (line != '\n'):
				package_lines.append(line.rstrip())
			else:
				p = Package(package_lines)
				package_objects[p.get_field("Package")] = p
				package_lines = []
    except:
        raise

def analyze_packages_file(path):
	for p in package_objects:
		deb = Deb(path, package_objects[p])
		if not deb.verify_deb():
			pool_deb(deb.get_filename(), deb.get_download_uri())

def analyze_packages_file_wget(path):
	for p in package_objects:
		deb = Deb(path, package_objects[p])
		if not deb.verify_deb():
			cmd = wget+deb.get_download_uri()+' -O '+deb.get_filename()
			jobs.append(cmd)

def download_deb(filename, url):
    try:
        print "downloading %s from %s" % (filename, url)
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            print "--- content type is %s" % r.headers['content-type']
            if 'text/html' in r.headers['content-type']:
                return False
            else:
                try:
                    print "uri: %s" % url
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk: # filter out keep-alive new chunks
                                f.write(chunk)
                                f.flush()
                    print "downloaded %s filename" % filename
                    print "done."
                    return True
                except (KeyboardInterrupt, SystemExit):
                    raise
    except IOError:
        print "Name or service not known"

def call_command(command):
    os.system(command)

def pool_deb(filename, uri):
    try:
        job_args = [ filename, uri ]
        cmd = multiprocessing.Process(target=download_deb, args=job_args)
        jobs.append(cmd)
        cmd.start()
    except:
        raise

'''
Help
'''
def usage ():
    print('Usage: check_mirror.py --suite <suite> --directory <directory> --arch <arch>')

'''
Start checking of Debian repository (using wget to download)
'''
def test_mirror_wget(path, suite, arch):
	print " = start checking Debian mirror consistency = "
	try:
		for s in suite:
			for section in sections:
				for a in arch:
					arch_folder = "binary-"+a
					d = os.path.join(path, "dists", s, section, arch_folder)
					if os.path.exists(d):
						packages = os.path.join(d, "Packages.bz2")
						if os.path.isfile(packages):
							f = bz2.BZ2File(packages, 'r')
							parse_packages_file(f)
							f.close()
							analyze_packages_file_wget(path)
						else:
							print "error: Packages file %s is missing" % packages
							continue
					else:
						print "error: Architecture %s not exists in this repository" % arch_folder
						continue
		print("{} wget jobs queued".format(len(jobs)))
		pool = Pool(processes=maxjobs)
		pool.map(call_command, jobs)
	except:
		raise

'''
Start checking of Debian repository
'''
def test_mirror(path, suite, arch):
	print " = start checking Debian mirror consistency = "
	try:
		for s in suite:
			for section in sections:
				for a in arch:
					arch_folder = "binary-"+a
					d = os.path.join(path, "dists", s, section, arch_folder)
					if os.path.exists(d):
						packages = os.path.join(d, "Packages.bz2")
						print "Analyzing Packages file %s" % packages
						if os.path.isfile(packages):
							f = bz2.BZ2File(packages, 'r')
							parse_packages_file(f)
							f.close()
							analyze_packages_file(path)
							for j in jobs:
								j.join()
						else:
							print "error: Packages file %s is missing" % packages
							continue
					else:
						print "error: Architecture %s not exists in this repository" % arch_folder
						continue
	except (KeyboardInterrupt, SystemExit):
		print "Caught KeyboardInterrupt, terminating workers"
		for j in jobs:
			j.join()
	except:
		raise

'''
Main Function
'''
def main(argv):
	try:
		opts, args = getopt.getopt(argv,"hs:d:a:",["suite=","directory=","arch=", "help"])
		for o,val in opts:
			if o in ("-a", "--arch"):
				archs = val.split(',')
			elif o in ("-d", "--directory"):
				repo_path = val
			elif o in ("-s", "--suite"):
				suites = val.split(',')
			else:
				usage()
				sys.exit()
		if not repo_path:
			repo_path = os.getcwd()
		# start checking
		test_mirror_wget(repo_path, suites, archs)
	except getopt.GetoptError:
		usage()
		sys.exit(2)

if __name__ == "__main__":
	main(sys.argv[1:])
