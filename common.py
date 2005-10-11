#!/usr/bin/python

###################################################################################
#                          progressbar.py  -  description
#                             -------------------
#    begin                : Oct  4, 2005
#    last update          : Oct  4, 2005
#    copyright            : (C) 2005 by Luis Useche
#    email                : useche@gmail.com
#
###################################################################################
#     This file is part of Postzilla.
#
#     Postzilla is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     Foobar is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Foobar; if not, write to the Free Software
#     Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
###################################################################################

import os
import sys

from urlparse import urlparse

from httplib import HTTPConnection
from ftplib  import FTP

import string, base64

from download import HttpDownloadPart, FtpDownloadPart

def join_files(file,chunks):
    complete_file = open(file,"w")
    for f in ["%s.%d"%(file,i) for i in range(chunks)]:
        partial_file = open(f,"r")
        complete_file.write(partial_file.read())
        partial_file.close()
    complete_file.close()

def delete_temp_files(file,chunks):
    map(lambda f: os.remove(f),["%s.%d"%(file,i) for i in range(chunks)])

def get_file_size(url, user, password):
    parsedURL = urlparse(url)

    if parsedURL[0] == 'http':
        conn = HTTPConnection(parsedURL[1])

        #authentication
        extra_headers = {}
        if user and password:
            extra_headers = {'Authorization': 'Basic %s'%string.strip(base64.encodestring(user + ':' + password))}
        
        conn.request('GET',parsedURL[2],headers=extra_headers)
        r = conn.getresponse()

        #verify that the request go well
        verify_http_response(r)

        length = r.length
        
        conn.close()

    elif parsedURL[0] == 'ftp':

        print "Connecting to %s..."%(parsedURL[1])
        ftp = FTP(parsedURL[1])

        print "Login..."
        #authentication stuff
        if user and password:
            response = ftp.login(user,password)
        else:
            response = ftp.login()

        #verify that the login was right
        verify_ftp_response(response)

        length = ftp.size(parsedURL[2])

        ftp.quit()

    else:
        error_exit('We only support ftp and http protocols')

    return length

def get_download_protocol(url):
    parsedURL = urlparse(url)
    if parsedURL[0] == 'http':
        return HttpDownloadPart
    else:
        return FtpDownloadPart

def verify_http_response(res):
    if res.status!=200 and res.status!=206:
        if res.status==401:
            error_exit('You must supply the corrects user and password')
        else:
            error_exit('There is some error with the server reques. HTTP error: %s'%res.status)

def verify_ftp_response(response):
    if not '230' in response:
        error_exit('Error make login in ftp server. Verify your user, password and url')

def error_exit(msg):
    print >> sys.stderr, msg
    sys.exit(-1)

#Python 2.2 and previous do not have enumerate
if(sys.version_info < (2,3)):
    def enumerate(list):
        out = []
        i = 0
        for x in list:
            out.append((i,x))
            i = i + 1
        return out