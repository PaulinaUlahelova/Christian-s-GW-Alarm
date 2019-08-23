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
import scipy.constants
import matplotlib.pyplot as plt
import numpy as np


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
    MassGap=StringCol(30)
    Revision=StringCol(30)
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
    if root.attrib['role'] != 'observation':
        return
    #acknowledge
    #print('I have received a notice!')
    
    #ensure correct working directory and open the table
    if os.path.basename(os.getcwd()) != "event_data":
        try:
            os.chdir('./event_data')
        except:
            os.mkdir('./event_data')
            os.chdir('./event_data')    
    while True:
        try:
            h5file = open_file("Event Database",mode="a",title="eventinfo")
            break
        except ValueError:
            print("file in use... trying again in 5s")
            time.sleep(5)
    try:
        h5file.create_group("/",'events')
    except NodeError:
        pass
    
    # Read all of the VOEvent parameters from the "What" section.
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}
    descs = [elem.text for elem in root.iterfind('.//Description')]

        
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
    htmllinks=[]
    
    if any('LALInferenceOffline.png' in s for s in all_files):
        imglinks = [s for s in all_files if 'LALInferenceOffline.png' in s]
    else:
        imglinks = [s for s in all_files if 'bayestar.png' in s]
    imgfile = imglinks[-1]
    imgfilepath = "https://gracedb.ligo.org"+imgfile
    os.system("curl -0 "+imgfilepath + '> ' + './'+skymap)

    #os.system("curl -0 "+filepath + '> ' + fitspath)
    #os.system("ligo-skymap-plot map_to_convert.fits.gz"+" -o "+skymap+" --annotate --contour 50 90 --geo")
    try:
        table = h5file.create_table(h5file.root.events,params['GraceID'],Event,'CBC event')
    except:
        table=h5file.get_node("/events",params['GraceID'])
        
    if any('bayestar.html' in s for s in all_files):
        htmllinks = [s for s in all_files if 'bayestar.html' in s]
    htmlfile = htmllinks[-1]
    htmlfilepath = "https://gracedb.ligo.org"+htmlfile
    r2 = requests.get(htmlfilepath)
    soup2 = BeautifulSoup(r2.text,"lxml")
    for col in soup2.tbody.find_all("tr"):
        if 'DISTMEAN' in str(col):
            dist = col.text.split('\n')[2]
            dist = str("{0:.3f}".format(float(dist)))
        elif 'DISTSTD' in str(col):
            diststd = col.text.split('\n')[2]
            diststd= str("{0:.3f}".format(float(diststd)))
    finaldist = dist + ' +- '+diststd + ' Mpc'
    
    det_event = table.row
    lookoutfor = ['BBH','BNS','MassGap','NSBH','Terrestrial']
    lookoutfor2=['HasNS','HasRemnant']
    order = []
    order2=[]
    vals = []
    vals2=[]
    descriptions={}
    # Print all parameters.
    i=0
    
    print(params['GraceID'])
    
    for key, value in params.items():
        #print(key, '=', value)
        if key == 'FAR':
            per_yr = float(value)*scipy.constants.year
            if per_yr <= 1:
                oneinyr = 1/per_yr
            else:
                oneinyr = per_yr
            if len(str(oneinyr).split('.')[0]) >= 5 or 'e' in str(oneinyr):
                val = "One every "+str("{0:.2e}".format(oneinyr))+" yrs"
            else:
                val = "One every "+str("{0:.3f}".format(oneinyr))+" yrs"
            det_event[key] = val
            descriptions[key]=descs[i]
        elif key == 'Pkt_Ser_Num':
            key = 'Revision'
            det_event[key] = value
            descriptions[key] = descs[i]
        elif key in lookoutfor:
            order.append(key)
            vals.append(float(value))
            det_event[key]=str("{0:.3f}".format(float(value)*100))+'%'
            descriptions[key]=descs[i]
        elif key in lookoutfor2:
            order2.append(key)
            vals2.append(float(value))
            if float(value) < 0.001:
                det_event[key] = '< 0.1%'
            else:  
                det_event[key]=str("{0:.2f}".format(float(value)*100))+'%'
            descriptions[key]=descs[i]
        else:
            try:
                det_event[key] = value
                descriptions[key]=descs[i]
            except:
                i+=1
                continue
        i+=1
    #print(descriptions)
    det_event['skymap'] = skymap
    det_event['Distance'] = finaldist
    det_time = root.find('.//ISOTime')
    det_text = det_time.text
    [one,two] = det_text.split('T')
    one=one.replace(':','-')
    two = two.split('.')[0]
    det_formtime = one+' at '+two
    
    det_event['DetectionTime']=det_formtime

    upt_time = root.find('.//Date')
    upt_text = upt_time.text
    [one1,two1] = upt_text.split('T')
    one1=one1.replace(':','-')
    two1=two1.split('.')[0]
    upt_formtime = one1+' at '+two1
    det_event['UpdateTime'] = upt_formtime
        
    #save the pie of possibilities
    specindex = np.argmax(vals)
    
    fig1, ax1 = plt.subplots(figsize=(5,5))
    ax1.pie(vals,labels=order,wedgeprops=dict(width=0.5),labeldistance=None)
    ax1.axis('equal')
#    plt.text(0,0.1,'Type:',fontsize=20,transform=ax1.transAxes)
#    plt.text(0,0,order[specindex],fontsize=20,transform=ax1.transAxes)
    plt.text(0.365,0.55,'Event Type:',transform=ax1.transAxes,fontsize=16)
    if order[specindex] == 'NSBH':
        plt.text(0.395,0.42,order[specindex],fontsize=26,transform=ax1.transAxes)
    elif order[specindex] == 'Terrestrial':
        plt.text(0.335,0.44,order[specindex],fontsize=22,transform=ax1.transAxes)
    elif order[specindex] == 'MassGap':
        plt.text(0.335,0.44,order[specindex],fontsize=26,transform=ax1.transAxes)
    else:
        plt.text(0.42,0.42,order[specindex],fontsize=28,transform=ax1.transAxes)

    plt.text(0,0.05,'Event Type',fontsize=13,transform=ax1.transAxes)
    plt.text(0,0.01,'Probability Distribution',fontsize=13,transform=ax1.transAxes)

    plt.tight_layout()
    plt.savefig(params['GraceID']+'_pie.png')
    
#    pos=[0,1]
#    tickpos=np.array([0,0.2,0.4,0.6,0.8,1])*100
#    data = np.array(vals2)*100
#    
#    fig2,ax2 = plt.subplots(figsize=(4,1.5))
#    # Hide the right and top spines
#    ax2.spines['right'].set_visible(False)
#    ax2.spines['top'].set_visible(False)
#    
#    # Only show ticks on the left and bottom spines
#    ax2.yaxis.set_ticks_position('left')
#    ax2.xaxis.set_ticks_position('bottom')
#    ax2.barh(pos,data,height=0.7,color=['C8','C9'])
#    plt.xlabel('Probability (%)')
#    plt.xticks(tickpos)
#    plt.yticks(pos,order2)
#    plt.tight_layout()
#    plt.savefig(params['GraceID']+'_bar.png')
    plt.close(fig1)
#    plt.close(fig2)
    
    det_event.append()
    table.flush()
    h5file.close()
    
    
#gcn.listen(host="209.208.78.170",handler=process_gcn)
#        
#        
#testing
#os.chdir('./event_data')
#import lxml
#payload = open('PreviousEventToRead.xml', 'rb').read()
#root = lxml.etree.fromstring(payload)
#process_gcn(payload, root)
