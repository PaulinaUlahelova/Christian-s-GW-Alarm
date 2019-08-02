#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:21:39 2019

@author: christian
"""

import gcn
from tables import *
import os
from bs4 import BeautifulSoup
import requests
import time


class Event(IsDescription):
    GraceID=StringCol(30)
    AlertType=StringCol(30)
    Instruments = StringCol(30)
    FAR = StringCol(30)
    skymap=StringCol(30)
    Group=StringCol(30)
    BNS=StringCol(30)
    NSBH=StringCol(30)
    BBH=StringCol(30)
    Terrestrial = StringCol(30)
    HasNS=StringCol(30)
    HasRemnant=StringCol(30)
    Distance=StringCol(30)
    DetectionTime=StringCol(30)
    UpdateTime=StringCol(30)

# Function to call every time a GCN is received.
# Run only for notices of type
# LVC_PRELIMINARY, LVC_INITIAL, or LVC_UPDATE.
@gcn.handlers.include_notice_types(
    gcn.notice_types.LVC_PRELIMINARY,
    gcn.notice_types.LVC_INITIAL,
    gcn.notice_types.LVC_UPDATE,
    gcn.notice_types.LVC_RETRACTION)

def process_gcn(payload, root):
    
    # Respond only to 'test' events.
    # VERY IMPORTANT! Replace with the following code
    # to respond to only real 'observation' events.
    # if root.attrib['role'] != 'observation':
    #    return
    if root.attrib['role'] != 'observation':
        return
    #acknowledge
    print('I have received a notice!')
    
    #ensure correct working directory and open the table
    if os.path.basename(os.getcwd()) != "event_data":
        try:
            os.chdir('./event_data')
        except:
            os.mkdir('./event_data')
            os.chdir('./event_data')    
    h5file = open_file("Event Database",mode="a",title="eventinfo")
    try:
        h5file.create_group("/",'events')
    except NodeError:
        pass
    
    # Read all of the VOEvent parameters from the "What" section.
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    if params['AlertType'] == 'Retraction':
        #Remove the event info if a retraction is issued - we don't care anymore
        #FIXME: in future flag the event instead and display seperately for interest/ref
        h5file.remove_node("/events",params['GraceID'])
        h5file.close()
        return
    
    if params['Group'] != 'CBC':
        return
    
    #prepare path for localization skymap, then download and produce the map in png format
    #filepath = params['skymap_fits']
    #fitspath = './map_to_convert.fits.gz'
    
    filesurl = "https://gracedb.ligo.org/superevents/"+params['GraceID']+"/files/"
    skymap = params['GraceID']+'.png'
    r =requests.get(filesurl) 
    soup = BeautifulSoup(r.text,"lxml")
    
    all_files = [a['href'] for a in soup.find_all("a")]
    imglinks = []
    htmllink=[]

    if any('LALInferenceOffline.png' in s for s in all_files):
        imglinks = [s for s in all_files if 'LALInferenceOffline.png' in s]
    else:
        imglinks = [s for s in all_files if 'bayestar.png' in s]
    
    imgfile = imglinks[-1]
    
    imgfilepath = "https://gracedb.ligo.org"+imgfile
    
    os.system("curl -0 "+imgfilepath + '> ' + './'+skymap)

    #os.system("curl -0 "+filepath + '> ' + fitspath)
    #os.system("ligo-skymap-plot map_to_convert.fits.gz"+" -o "+skymap+" --annotate --contour 50 90 --geo")

    #group name: events

    try:
        table = h5file.create_table(h5file.root.events,params['GraceID'],Event,'CBC event')
    except:
        table=h5file.get_node("/events",params['GraceID'])
        
    det_event = table.row

    # Print all parameters.
    for key, value in params.items():
        print(key, '=', value)
        try:
            det_event[key] = value
        except:
            continue
    det_event['skymap'] = skymap
    #timing
    if params['AlertType'] == 'Preliminary':
        det_event['DetectionTime'] = str(time.time())
        det_event['UpdateTime'] = str(time.time())
    else:
        det_event['UpdateTime'] = str(time.time())
        
    det_event.append()
    table.flush()
    h5file.close()
    
#gcn.listen(host="209.208.78.170",handler=process_gcn)
#        
#        
##testing
#import lxml
#payload = open('MS181101ab-1-Preliminary.xml', 'rb').read()
#root = lxml.etree.fromstring(payload)
#process_gcn(payload, root)
