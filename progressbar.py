#!/usr/bin/python

###################################################################################
#                          progressbar.py  -  description
#                             -------------------
#    begin                : Sep 30, 2005
#    last update          : Oot  3, 2005
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

import struct, termios, fcntl, sys
from threading import Semaphore, Timer

class Part:
    """
    Keep all the information of a part/thread
    """
    def __init__(self, toDownload, columns, downloaded=0):
        self.toDownload = toDownload
        self.downloaded = downloaded
        self.columns = columns

class ProgressBar:
    """
    Implement a progress bar to see the advance of each thread

    Attributes:
    - barMutex:      semaphore to be sure that only one thread update the bar at time
    - part:          list that contains all parts of the download. Each part represent
                     a thread.
    - toDownload:    Total of bytes to download (size of the file).
    - downloaded:    number of bytes which had been downloaded
    - bar:           String that contains the bar

    Methods:
    - update:        method to be called for every thread to get update on the progressbar
    - updateBar:     generate the self.bar attribute with all parts information and progressbar
                     information
    - finalize:      complete the bar and print an \n
    """
    
    def __init__(self, lpairs):
        #subtract 5 characters for percent,  2 character for '[' and ']' and 10 for download rate
        self.columns = get_term_size()-17

        #semaphore to mutex the bar update and downloaded variable
        self.barMutex = Semaphore()
        self.downloadedMutex = Semaphore()

        #initialize all parts and calculate the total bytes to download
        columns_part = self.columns/len(lpairs)
        self.part = []
        self.toDownload = 0
        for p in lpairs:
            temp = p[1]-p[0]
            self.part.append(Part(temp,columns_part))
            self.toDownload += temp

        #add the rest of bar characters to the last thread
        self.part[-1].columns += self.columns%len(lpairs)

        self.downloaded = 0

        #download rate variables
        self.rate ='     0b/s'
        self.oldDownloaded = 0
        self.speedometer = Timer(1,self.updateRate)
        self.speedometer.start()

        self.oldbar = None
        self.updateBar()

    def update(self, order, bytesAdded):
        #first update the part
        self.part[order].downloaded += bytesAdded

        ################################################
        self.downloadedMutex.acquire() #initiate mutex over the downloaded variable
        ################################################
        
        self.downloaded += bytesAdded

        ################################################
        self.downloadedMutex.release()
        ################################################
        
        #update the bar
        self.updateBar()
        
    def updateBar(self):
        ################################################
        self.barMutex.acquire() #initiate the bar mutex (so many threads updating the bar)
        ################################################

        self.bar = "["

        #generating minibars for every thread
        for p in self.part:
            blackCharacters = int((p.downloaded/float(p.toDownload))*p.columns)
            self.bar += "="*blackCharacters + " "*(p.columns-blackCharacters)

        self.bar += "] "

        #making porcentage
        porcentage = "%d%%"%int((self.downloaded/float(self.toDownload))*100)
        porcentage = " "*(4-len(porcentage)) + porcentage

        self.bar += porcentage + " "

        self.bar += self.rate

        self.bar += "\r"

        #print it only if change
        if not self.oldbar == self.bar:
            printStdout(self.bar)
            self.oldbar = self.bar

        ###############################################
        self.barMutex.release() #release the bar mutex
        ###############################################
        
    def updateRate(self):
        bytesPsec = self.downloaded - self.oldDownloaded
        self.rate = humanize_rate(bytesPsec)
        self.rate = " "*(9-len(self.rate)) + self.rate

        self.updateBar()

        self.oldDownloaded = self.downloaded

        self.speedometer = Timer(1,self.updateRate)
        self.speedometer.start()

    def finalize(self):
        self.downloaded = self.toDownload
        self.updateBar()
        print "" # printing the \n
        self.speedometer.cancel()

def humanize_rate(rate):
    if rate>=1048576:
        rate /= 1048576.0
        return "%.1fM/s"%rate
    elif rate >= 1024:
        rate /= 1024.0
        return "%.1fK/s"%rate
    else:
        return "%.1fb/s"%rate

def get_term_size():
    "Get the term's number of columns"
    s = struct.pack("HHHH", 0, 0, 0, 0)
    cols = struct.unpack("HHHH", fcntl.ioctl(sys.stdout,termios.TIOCGWINSZ, s))[1]
    return cols

def printStdout(msg):
    "Write a string to the stdout (print raise an \n on its message)"
    sys.stdout.write(msg)
    sys.stdout.flush()
