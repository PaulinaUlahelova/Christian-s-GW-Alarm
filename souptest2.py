#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 10:30:58 2019

@author: christian
"""
from bs4 import BeautifulSoup
import requests
from gcn_test import process_gcn
import os
import lxml

#Get old links by parsing properly, and download + save to file!

if os.path.basename(os.getcwd()) != "event_data":
    try:
        os.chdir("./event_data")
    except:
        os.mkdir("./event_data")
        os.chdir("./event_data")
        

url = "https://gracedb.ligo.org/superevents/public/O3/"
r =requests.get(url) 
soup = BeautifulSoup(r.text,"lxml")

eventlinks = []
eventnames = []

def hasstylenotclass(tag):
    return tag.has_attr('style') and not tag.has_attr('class')

for col in soup.tbody.find_all("tr"):
    #print(row)
    #for col in row("tr"):
    if 'RETRACTED' in str(col):
        continue
    #link = col.find(hasstylenotclass).a.extract()
    name = col.find(hasstylenotclass).a.string
    eventnames.append(name)
    eventlinks.append("https://gracedb.ligo.org/superevents/"+name+"/files/")


for i,link in enumerate(eventlinks):
    r =requests.get(link) 
    soup = BeautifulSoup(r.text,"lxml")
    
    all_files = [a['href'] for a in soup.find_all("a")]
    
    bestfiles = []
    imglinks = []
    htmllink=[]

    if any('Update' in s for s in all_files):
        bestfiles = [s for s in all_files if 'Update' in s]
    elif any('Initial' in s for s in all_files):
        bestfiles= [s for s in all_files if 'Initial' in s]
    else:
        bestfiles = [s for s in all_files if 'Preliminary' in s]
        
    if any('LALInferenceOffline.png' in s for s in all_files):
        imglinks = [s for s in all_files if 'LALInferenceOffline.png' in s]
    else:
        imglinks = [s for s in all_files if 'bayestar.png' in s]
    
    imgfile = imglinks[-1]
    datafile = bestfiles[-1]
    
    imgfilepath = "https://gracedb.ligo.org"+imgfile
    datafilepath = "https://gracedb.ligo.org"+datafile
    
    imgpath = eventnames[i]+'.png'
    datapath = 'PreviousEventToRead.xml'
    os.system("curl -0 "+datafilepath + '> ' + './'+datapath)
    os.system("curl -0 "+imgfilepath + '> ' + './'+imgpath)
    
    payload = open(datapath,'rb').read()
    root=lxml.etree.fromstring(payload)
    process_gcn(payload,root)


    
    