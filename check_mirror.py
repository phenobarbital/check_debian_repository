#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
check_mirror
Check for Debian repository consistency

Autor: Jesus Lara
Correo: jesuslarag@gmail.com
Licencia: GPL Version 3
Version: 0.1

usage: check_mirror.py -s wheezy -a arch(ej: amd64) -d /path/to/repository
'''

import os
import sys, getopt
import gzip
import re
import requests
import multiprocessing
import magic
import random
import signal

from check_config import config

configdata = config("checkrepo.conf")
datamirrors = configdata.ShowItemSection("mirrors")
mirrors = []
for i in range(len(datamirrors)):
    mirrors.append(mirrors[i][1])

arch = configdata.ShowValueItem("repo","arch").split(",")
sections = configdata.ShowValueItem("repo","sections").split(",")
maxjobs = int(configdata.ShowValueItem("conf","maxjobs"))
exclude_dbg = configdata.ShowValueItem("conf","exclude_dbg") == "True"
suites = configdata.ShowValueItem("repo","suites").split(",")

# test suite

#mirrors = [ "http://debian.mirror.constant.com/debian/", "http://mirror.us.leaseweb.net/debian/",  "http://debian.mirror.gtcomm.net/debian/", "http://mirrors.advancedhosters.com/debian/", "http://mirror.cc.columbia.edu/debian/", "http://debian.uniminuto.edu/debian/"  ]
#sections=('main', 'contrib', 'non-free')
#exclude_dbg=True

#maxjobs = 6                 # maximum number of concurrent jobs
jobs = []                   # current list of queued jobs
jobs_args = []

def usage ():
    print('Usage: check_mirror.py --suite <suite> --directory <directory> --arch <arch>')

def verify_deb(filename):
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        # create directory
        os.makedirs(d)
    if "-dbg" in filename:
        return True
    if ( not os.path.isfile(filename)):
        print "verify_deb: filename %s is missing" % filename
        return False
    else:
        # verify mime format
        if 'Debian binary package' in magic.from_file(filename):
            return True
        else:
            # delete fake file
            print "verify_deb: removing fake file %s" % filename
            os.remove(filename)
            return False
    return True

def download_deb(filename, url):
    try:
        print "downloading %s from %s" % (filename, url)
        r = requests.get(url, stream=True)
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

def get_download_uri(filename):
    mirror = random.choice(mirrors)
    return mirror+filename

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def pool_deb(filename, uri):
    try:
        job_args = [ filename, uri ]
        cmd = multiprocessing.Process(target=download_deb, args=job_args)
        jobs.append(cmd)
        cmd.start()
    except:
        raise

def test_mirror(ruta, suites, archs):
    print " = start checking Debian mirror consistency = "
    ''' check mirror '''
    try:
        for suite in suites:
            for section in sections:
                for a in archs:
                    arch = "binary-"+a
                    d = os.path.join(ruta, "dists", suite, section, arch)
                    if os.path.exists(d):
                        packages = os.path.join(d, "Packages.gz")
                        if os.path.isfile(packages):
                            f = gzip.open(packages, 'rb')
                            for line in iter(f):
                                if re.match("^Filename:", line):
                                    filename = line[10:len(line)-1]
                                    urlfile = get_download_uri(filename)
                                    p = os.path.join(ruta, filename)
                                    if not verify_deb(p):
                                    #job_args = [ p, urlfile ]
                                    # download_deb(p, urlfile)
                                    #cmd = multiprocessing.Process(target=download_deb, args=job_args)
                                    #jobs.append(cmd)
                                    #cmd.start()
                                        pool_deb(p, urlfile)
                            f.close()
                            for j in jobs:
                                j.join()
                    else:
                        print "error: path %s not exists" % d
    except (KeyboardInterrupt, SystemExit):
        print "Caught KeyboardInterrupt, terminating workers"
        for i in jobs:
            j.join()
    except:
        raise

def main(argv):
    ruta = ''
    suites = ''
    archs = ''
    try:
        opts, args = getopt.getopt(argv,"hs:d:a:",["suite=","directory=","arch=", "help"])
        for o,a in opts:
            if o in ("-a", "--arch"):
                archs = a.split(',')
            elif o in ("-d", "--directory"):
                ruta = a
            elif o in ("-s", "--suite"):
                suites = a.split(',')
            else:
                usage()
                sys.exit()
        # check dictionaries
        if not archs:
            archs = ('amd64', 'i386', 'armhf', 'mipsel')
        if not suites:
            suites=('wheezy', 'jessie')
        if not ruta:
            ruta = os.getcwd()
        # check mirror consistency
        test_mirror(ruta, suites, archs)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

if __name__ == "__main__":
   #main(sys.argv[1:])
   repodeb = Repodeb("check_debian_repository.conf")
   repodeb.Imprimir()
