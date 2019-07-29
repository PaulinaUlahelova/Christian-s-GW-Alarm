#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:21:39 2019

@author: christian
"""

import gcn
#import healpy as hp
from tables import *
#import numpy as np
#import ligo.skymap
import os
#import re

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
    if root.attrib['role'] != 'test':
        return
    #acknowledge
    print('I have received a notice!')
    
    #ensure correct working directory and open the table
    os.chdir(os.path.dirname(__file__))
    try:
        os.chdir('./event_data')
    except:
        os.mkdir('./event_data')
        os.chdir('./event_data')    
    h5file = open_file("Event Database",mode="a",title="eventinfo")
    
    # Read all of the VOEvent parameters from the "What" section.
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    # Respond only to 'CBC' events. Change 'CBC' to "Burst'
    # to respond to only unmodeled burst events.
    
    if params['AlertType'] == 'Retraction':
        #Remove the event info if a retraction is issued - we don't care anymore
        #FIXME: in future flag the event instead and display seperately for interest/ref
        #table = h5file.get_node("/events",params['GraceID'])
        #table.remove_rows(start=0)
        h5file.remove_node("/events",params['GraceID'])
        #table.flush
        h5file.close()
        return
    
    if params['Group'] != 'CBC':
        return
    
    #prepare path for localization skymap, then download and produce the map in png format
    filepath = params['skymap_fits']
    fitspath = './map_to_convert.fits.gz'
    skymap = params['GraceID']+'.png'
    
    os.system("curl -0 "+filepath + '> ' + fitspath)
    os.system("ligo-skymap-plot map_to_convert.fits.gz"+" -o "+skymap+" --annotate --contour 50 90 --geo")

    #group name: events
    #first-time special case, for if group not made
    try:
        h5file.create_group("/",'events')
    except NodeError:
        pass
    try:
        table = h5file.create_table(h5file.root.events,params['GraceID'],Event,'CBC event')
        print("ok")
    except:
#        for leaf in h5file.root.events._f_walknodes('Leaf'):
#            s = str(leaf)
#            s2 = re.search('/events/(.*) ', s).group(1)
#            print(s2)
#            print(params['GraceID'])
#            if s2 == params['GraceID']:
#                test = leaf.rsplit(' ',1)[0]
#                table = h5file.root.test
        #table=getattr(h5file.root.events,params['GraceID'])
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

 #   if 'skymap_fits' in params:
  #      # Read the HEALPix sky map and the FITS header.
    #    skymap, header = hp.read_map(params['skymap_fits'],
   #                                  h=True, verbose=False)
  #      header = dict(header)
#
        # Print some values from the FITS header.
    #    print('Distance =', header['DISTMEAN'], '+/-', header['DISTSTD'])
        
    table.flush()
    h5file.close()
    
gcn.listen(handler=process_gcn)
        
#testing
#import lxml
#payload = open('MS181101ab-1-Preliminary.xml', 'rb').read()
#root = lxml.etree.fromstring(payload)
#process_gcn(payload, root)
