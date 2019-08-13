#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 17:04:33 2019

@author: christian
"""

import kivy
kivy.require('1.11.0')

from kivy.config import Config
Config.set('graphics','width','800')
Config.set('graphics','height','480')
Config.set('kivy','default_font',[
           './fonts/OpenSans-Light.ttf','./fonts/OpenSans-Regular.ttf','./fonts/OpenSans-LightItalic.ttf',
           './fonts/OpenSans-Bold.ttf'])

import threading
import time
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty, ObjectProperty, StringProperty, AliasProperty, DictProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup
from kivy.uix.behaviors  import ButtonBehavior, ToggleButtonBehavior
from kivy.animation import Animation

#import RPi.GPIO as GPIO
from kivy.lang.builder import Builder

from detector_monitorv2 import statusdetect
from sync_database import sync_database
import gcn
from gcn_test import process_gcn
import requests
from bs4 import BeautifulSoup
from tables import * 
import datetime
import os
import re
import numpy as np

class Event(IsDescription):
    AlertType=StringCol(30)
    BBH=StringCol(30)
    BNS=StringCol(30)
    FAR = StringCol(30)
    GraceID=StringCol(30)
    Group=StringCol(30)
    HasNS=StringCol(30)
    HasRemnant=StringCol(30)
    Instruments = StringCol(30)
    MassGap=StringCol(30)
    NSBH=StringCol(30)
    Terrestrial = StringCol(30)
    skymap=StringCol(30)
    DetectionTime=StringCol(30)
    UpdateTime=StringCol(30)
    MassGap=StringCol(30)
    Distance=StringCol(30)
    Revision=StringCol(30)
    
#FIXME: DECLARE ALL GPIO PINS AND INITIAL INS/OUTS HERE
    

global flag
global main_flag
global newevent_flag
flag = 0
main_flag=0
newevent_flag=0

Builder.load_file('GWalarm.kv')

class MainButton(Button):
    name=ObjectProperty()
    def nav(self):
        app=App.get_running_app()
        app.root.transition=SlideTransition()
        if self.name=='history':
            app.root.current='history'
        elif self.name=='status':
            app.root.current='status'
        elif self.name=='main':
            app.root.current='main'
        elif self.name=='plots':
            app.root.current='plots'
class MainScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout=GridLayout(cols=2,rows=2,padding=30,spacing=30,row_default_height=150)
        with layout.canvas.before:
            Color(.2,.2,.2,1)
            self.rect=Rectangle(size=(800,600), pos=layout.pos)
            
        def stop(obj):
            global main_flag
            main_flag=1
            App.get_running_app().stop()

        self.add_widget(layout)
        ids=('history','status','plots')
        texts=('Event History','Detector Status','Test Plots')
        [layout.add_widget(MainButton(text=texts[i],name=ids[i])) for i in range(0,len(ids))]
        quitButton=Button(text='Quit')
        quitButton.bind(on_press=stop)
        layout.add_widget(quitButton)
        
        def event_waiting():
            '''New event popup handler'''
            global newevent_flag
            global main_flag
            newevent_flag=0
            main_flag=0
            while True:
                while True:
                    #check for the flag once per minute (same rate the file is polled)
                    if newevent_flag == 1:
                        newevent_flag=0
                        #skip a level up to execute the rest of the loop, then back to waiting.
                        print('New event has been detected!!')
                        break
                    if main_flag == 1:
                        print('Event listener #2 closing...')
                        #return takes you right out of the function
                        return
                    time.sleep(5)
                
                #Read in the new event
                if os.path.basename(os.getcwd()) != "event_data":
                    try:
                        os.chdir("./event_data")
                    except:
                        os.mkdir("./event_data")
                        os.chdir("./event_data")
                while True:
                    try:
                        h5file = open_file("Event Database",mode="r",title="eventinfo")
                        break
                    except:
                        print("file in use... trying again in 5s")
                        time.sleep(5)
                try:
                    h5file.root.events
                except NoSuchNodeError:
                    time.sleep(5)
                    pass      
                
                #parse the event data file for the most recent event to be loaded: that's the name
                file = open("PreviousEventToRead.xml").read()
                def search(line):
                    result = re.search('<Param name="GraceID" dataType="string" value=(.*)ucd="meta.id">\n',
                                       str(line))
                    return result.group(1)
                eventid = search(file)
                print(str(eventid))
                for tab in h5file.list_nodes("/events"):
                    print(tab.name)
                    if str(tab.name) in eventid:
                        new_event_table=tab
#                    if tab.name == eventid:
#                        new_event_table = tab
                namelist = new_event_table.colnames
                new_event_row = new_event_table[-1]
                orderedrow = []
                for key in namelist:
                    orderedrow.append(new_event_row[key].decode()) 
                pop = InfoPop(title='New Event Detected!',namelist=namelist,row=orderedrow)
                pop.open()
                h5file.close()
        
        event_waiting_thread = threading.Thread(target=event_waiting)
        event_waiting_thread.start()
        
class HisColLabel(ToggleButtonBehavior,Label):
    sorttype=ObjectProperty()
    newsort=ObjectProperty()
    names=ObjectProperty()
    specialnames=ObjectProperty()
    primed=NumericProperty()
    
    def on_press(self):
#        self.primed = 1
        for child in self.parent.children:
            child.imgsource='./neutral.png'
    
    def on_state(self,widget,value):
        Clock.schedule_once(lambda dt:self.on_state_for_real(widget,value),0)
    def on_state_for_real(self,widget,value):
        print('Pressed' )
        print(self.primed)
#        if self.primed == 1:
        global flag
        flag = 1
        if value == 'down':
            self.newsort = self.sorttype+' Descending'
            self.imgsource='./ascending.png'

        else:
            self.newsort = self.sorttype+' Ascending'
            self.imgsource='./descending.png'
        #time.sleep(0.1)
        t2 = threading.Thread(target=historyUpdate,args=(App.get_running_app().root.children[0].children[0].children[1].children[0],
                                                         self.names,self.specialnames,self.newsort),daemon=True)
        t2.start()
#        elif self.primed == 0:
#            self.imgsource='./neutral.png'
#        self.primed=0


class HistoryScreen(Screen):    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(rows=3)
        self.add_widget(layout)
        
        if os.path.basename(os.getcwd()) != "event_data":
            try:
                os.chdir("./event_data")
            except:
                os.mkdir("./event_data")
                os.chdir("./event_data")    
                
        while True:
            try:
                h5file = open_file("Event Database",mode="r",title="eventinfo")
                break
            except:
                print("file in use... trying again in 5s")
                time.sleep(5)
        try:
            h5file.root.events
        except NoSuchNodeError:
            time.sleep(5)
            pass
        #grab a table, it doesn't matter which one!
        x=0
        for table in h5file.iter_nodes(where="/events",classname="Table"):
            tables=table
            if x==0:
                break
        
        def receive():
                #host="209.208.78.170"  
                gcn.listen(host="209.208.78.170",handler=process_gcn)
        t4 = threading.Thread(target=receive,daemon=True)
        t4.start()
        
        names = tables.colnames
        num_events = len(h5file.list_nodes(where="/events",classname="Table"))
        h5file.close()
        nameLay = GridLayout(cols=len(names),size_hint_y=0.1)
        specialnames=['GraceID','Distance','Instruments','FAR','UpdateTime']
        for name in specialnames:
            lab = HisColLabel(text=name,color=(0,0,0,1),sorttype=name)
            lab.names=names
            lab.specialnames=specialnames
            nameLay.add_widget(lab)
        layout.add_widget(nameLay)
        hisScroll = ScrollView(do_scroll_x=False,do_scroll_y=True,size_hint=(1,0.7))
        layout.add_widget(hisScroll)
        hisGrid = GridLayout(rows=num_events*100,size_hint_y=None)
        hisGrid.bind(minimum_height=hisGrid.setter('height'))
        hisGrid.height=num_events*50
        hisScroll.add_widget(hisGrid)
        
        t2 = threading.Thread(target=historyUpdate,args=(hisGrid,names,specialnames),daemon=True)
        t2.start()
        '''backup stuff'''
        
        smalls=BoxLayout(size_hint_y=0.1)
        def refresh_all(arg):
            App.get_running_app().stop()
            App.get_running_app().root_window.close()
            print('shutdown')
            #time.sleep(5)
            sync_database()
            #Wait for it to finish....
            print('done - restart away')
        
        backupTestButton=Button(text='Back up database (takes ages)')
        smalls.add_widget(backupTestButton)
        
        def stupid(obj):
            content = Button(text='Ok')
            content.bind(on_press=refresh_all)
            confirm = Popup(title='Are you sure?',content=content,size_hint=(0.4,0.4))
            confirm.open()
            
        backupTestButton.bind(on_press=stupid) 
         
        button2 =MainButton(text='Main Menu',name='main')#,size_hint_y=0.1)
        smalls.add_widget(button2)
        layout.add_widget(smalls)

class DetGrid(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
            
class DetLabel(Label):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color([0,0,0,0])
        
class WrapLabel(Label):
    pass

class HeadingLabel(ToggleButtonBehavior,Label):
    def on_state(self,widget,value):
        if value == 'down':
            print('down')
        else:
            print('up')
    pass

class InfoPop(Popup):
    namelist=ObjectProperty()
    row=ObjectProperty()
        
class GlossLabel(BoxLayout):
    nom=ObjectProperty()
    desc=ObjectProperty()

class Glossary(ScrollView):
    descs = ListProperty()
    namelist = ListProperty()
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.finish_init,0)
    def finish_init(self,dt):
        descdict = {'GraceID': 'Identifier in GraceDB', 'AlertType': 'VOEvent alert type', 
            'Instruments': 'List of instruments used in analysis to identify this event', 
            'FAR': 'False alarm rate for GW candidates with this strength or greater', 
            'Group': 'Data analysis working group', 
            'BNS': 'Probability that the source is a binary neutron star merger (both objects lighter than 3 solar masses)', 
            'NSBH': 'Probability that the source is a neutron star-black hole merger (primary heavier than 5 solar masses, secondary lighter than 3 solar masses)', 
            'BBH': 'Probability that the source is a binary black hole merger (both objects heavier than 5 solar masses)', 
            'Terrestrial': 'Probability that the source is terrestrial (i.e., a background noise fluctuation or a glitch)', 
            'HasNS': 'Source classification: binary neutron star (BNS), neutron star-black hole (NSBH), binary black hole (BBH), MassGap, or terrestrial (noise)', 
            'HasRemnant': 'Probability that at least one object in the binary has a mass that is less than 3 solar masses',
            'Distance':'Posterior mean distance to the event (with standard deviation) in MPc',
            'DetectionTime':'The mean date & time at which the event was first detected',
            'UpdateTime': "The date & time of the most recent update to this event's parameters",
            'MassGap':"Compact binary systems with at least one compact object whose mass is in the hypothetical 'mass gap' between neutron stars and black holes, defined here as 3-5 solar masses.",
            'Revision':"The number of revisions (updates) made to this event's parameters"}
        descripts=[]
        names = []
        for key,value in descdict.items():
            names.append(key)
            descripts.append(value)
        self.namelist = sorted(names)
        self.descs=[x for _,x in sorted(zip(names,descripts))]
        layout2 = GridLayout(rows=len(self.descs),size_hint_y=None)
        #layout2.bind(minimum_height=self.setter('height'))
        for i in range(len(self.namelist)):
            #lab = WrapLabel(text=self.namelist[i]+':'+self.discs[i])
            #layout2.add_widget(lab)
            gloss = GlossLabel()
            gloss.nom=self.namelist[i]
            gloss.desc=self.descs[i]
            layout2.add_widget(gloss)
        self.add_widget(layout2)
        self.do_scroll_x=False
        #self.add_widget(layout)
        layout2.height=sum([c.height for c in layout2.children])+20
        
class EventContainer(ButtonBehavior,GridLayout):
    name=ObjectProperty()
    namelist=ListProperty(['test1','test2'])
    row = ListProperty(['test1','test2'])
    pop = ObjectProperty()
    img= StringProperty()
    text0=StringProperty('tobereplaced')
    text1=StringProperty('tobereplaced')
    text2=StringProperty('tobereplaced')
    text3=StringProperty('tobereplaced')
    text4=StringProperty('tobereplaced')

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.finish_init,0)
        
    def finish_init(self,dt):
        self.pop = InfoPop(title="Superevent Information",namelist=self.namelist,row=self.row)
        
    def details(self):
        self.pop.namelist = self.namelist
        self.pop.row = self.row
        self.pop.open()
def historyUpdate(obj,names,specialnames,sorttype='Time Descending'):
    '''An important function that is responsible for populating and repopulating the history screen.'''
    global flag
    global main_flag
    #reset stop flag
    main_flag=0
    if os.path.basename(os.getcwd()) != "event_data":
        try:
            os.chdir("./event_data")
        except:
            os.mkdir("./event_data")
            os.chdir("./event_data")    
        
    #initial check to ensure file exists with necessary groupings
    while True:
        try:
            h5file = open_file("Event Database",mode="r",title="eventinfo")
            break
        except:
            print("file in use... trying again in 5s")
            time.sleep(5)
    try:
        h5file.root.events
    except NoSuchNodeError:
        time.sleep(5)
        pass
    h5file.close()
    
    #initial stat
    stats = os.stat("./Event Database")
    lastaccess= stats.st_mtime
    first = 1
    while True:
        stats = os.stat("./Event Database")
        access = stats.st_mtime 
        if access != lastaccess or first == 1:
            lastaccess=access


            #Clear widgets
            #obj.clear_widgets()
            while True:
                try:
                    h5file = open_file("Event Database",mode="r",title="eventinfo")
                    break
                except:
                    print("file in use... trying again in 5s")
                    time.sleep(5)
            
            #get all tables
            tables = [table for table in h5file.iter_nodes(where="/events",classname="Table")]
            sort_vars = []
            
            '''Check the table list and compare with current labels to see if boxes need changed'''
            children = [child for child in obj.children]
            #ids IN THE DISPLAY
            widgetids = []
            for child in children:
                widgetids.append(child.name)
            #ids IN THE DATABASE
            presentids = [child[-1]['GraceID'].decode() for child in h5file.root.events]
            
            '''Iterate through all events, re-drawing row-by-row the history viewer'''
            for table in tables:
                row=table[-1]
                if 'Time' in sorttype:
                    sort_vars.append(row['UpdateTime'].decode().split()[0])
                elif 'Distance' in sorttype:
                    sort_vars.append(float(row['Distance'].decode().split()[0]))
                elif 'GraceID' in sorttype:
                    string = str(row['GraceID'].decode())
                    sort_vars.append(int(re.sub("[a-zA-Z]","",string)))
                elif 'FAR' in sorttype:
                    sort_vars.append(float(row['FAR'].decode().split()[2]))
                elif 'Instruments' in sorttype:
                    sort_vars.append(row['Instruments'].decode())
            if sort_vars != []:
                if 'Descending' in sorttype:
                    try:
                        tables = [x for _,x in sorted(zip(sort_vars,tables),key=len[0])]
                    except TypeError:
                        tables2=[]
                        sort_indexes = np.argsort(np.array(sort_vars))
                        for index in sort_indexes:
                            tables2.append(tables[index])
                        tables=tables2
                elif 'Ascending' in sorttype:
                    try:
                        tables = [x for _,x in reversed(sorted(zip(sort_vars,tables)))]
                    except TypeError:
                        tables2=[]
                        sort_indexes = reversed(np.argsort(np.array(sort_vars)))
                        for index in sort_indexes:
                            tables2.append(tables[index])
                        tables=tables2
            
            #print(widgetids,presentids)
            for i,table in enumerate(tables):
                #read in the last row (most up to date)
                row = table[-1]
                orderedrow = []
                for key in names:
                    orderedrow.append(row[key].decode())
                if row['GraceID'].decode() not in widgetids:
                    if first == 0:
                        '''LAZY SOLUTION - NOT VERY FUTUREPROOF''' #FIXME
                        '''NEW EVENT!!!'''
                        global newevent_flag
                        newevent_flag=1
                        
                    grid = EventContainer(cols=len(specialnames)+1,name=row['GraceID'].decode())
                    grid.namelist=names
#                    for i in range(len(specialnames)):
                        #string=row[specialnames[i]]
#                        if specialnames[i] == 'Distance':
#                            getattr(grid,'text'+str(i))=string.decode().replace('+-',u'\xb1')
                        #else:    
                        #FIXME: ADD NEAT TEXT BY PARSING INPUT TEXT
                            #getattr(grid,'text'+str(i)) = string.decode()
                            #lab2 = Label(text=decoded,color=(0,0,0,1),font_size=(16))
#                        lab2 = Label(text=getattr(grid,'text'+str(i)),color=(0,0,0,1),font_size=(16))
#                        grid.add_widget(lab2)
                    obj.add_widget(grid,i)
                else:
                    grid = obj.children[i]
                grid.row=orderedrow
                for i in range(len(specialnames)):
                    string=row[specialnames[i]]
                    if specialnames[i] == 'Distance':
                        setattr(grid,'text'+str(i),string.decode().replace('+-',u'\xb1'))
                    elif specialnames[i] == 'GraceID':
                        grid.name=string.decode()
                        setattr(grid,'text'+str(i),string.decode()) 
                    else:    
                    #FIXME: ADD NEAT TEXT BY PARSING INPUT TEXT
                        setattr(grid,'text'+str(i),string.decode())       
            for i,child in enumerate(children):
                if widgetids[i] not in presentids:
                    obj.remove_widget(child)
                #orderedrow = []
#                for key in names:
#                    orderedrow.append(row[key].decode())
#                grid.row=orderedrow
#                
#                for i in range(len(specialnames)):
#                    string=row[specialnames[i]]
#                    if specialnames[i] == 'Distance':
#                        decoded=string.decode().replace('+-',u'\xb1')
#                    else:    
#                    #FIXME: ADD NEAT TEXT BY PARSING INPUT TEXT
#                        decoded = string.decode()
#                    lab2 = Label(text=decoded,color=(0,0,0,1),font_size=(16))
#                    grid.add_widget(lab2)
#                obj.add_widget(grid,len(obj.children))
            obj.do_layout()
            print('Event History Updated...')
            h5file.close()
            #reset the flag
            first = 0

        waittime = 10
        i=0
        while i < waittime:
            if flag ==1:
                print('his_thread restart')
                flag=0
                return
            if main_flag ==1:
                print('history thread closing...')
                return
            i+=1
            time.sleep(1)
def statusupdate(obj):
    global main_flag
    main_flag=0
    while True:
        data = statusdetect()
        
        for i,elem in enumerate(data):
            setattr(obj,'det'+str(i+1)+'props',elem)
#        j=0
#        for child in obj.children:
#            if stats[j] != 2:
#                child.current_color=[1-stats[j],0,stats[j],1]
#            else:
#                child.current_color=[0,1,0,1]
#            with child.canvas:
#                    Color(rgba=child.current_color)
#            i=0
#            for label in child.children:
#                label.text=order[i][j]
#                i+=1
#            j+=1
        
        waittime = 300
        i = 0
        while i < waittime:
            if main_flag == 1:
                print('statusthread closing...')
                return
            i+=1
            time.sleep(1)

def plotupdate(obj):
    global main_flag
    main_flag=0
    while True:
        if os.path.basename(os.getcwd()) != 'event_data':
            try:
                os.chdir("./event_data")
            except:
                os.mkdir("./event_data")
                os.chdir("./event_data")
        #formulate the url to get today's
        date = datetime.datetime.today()
        sort_date = [str(date.year),str(date.month).zfill(2),str(date.day).zfill(2)]
        datestring = sort_date[0]+sort_date[1]+sort_date[2]
        url = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/"
        url2 = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/instrument_performance/analysis_time/"
        #grab the soup and parse for links + descripts
        try:
            resp=requests.get(url)
            r = resp.text
            soup=BeautifulSoup(r,"lxml")
            resp2 = requests.get(url2)
            r2 = resp2.text
            soup2 = BeautifulSoup(r2,"lxml")
        except:
            print("URL Error: URL to the Range plots is broken : check online")
        obj.clear_widgets()
                
        sources=[]
        descripts=[]
        for link in soup.find_all("a"):
            linkstr = str(link.get("href"))
            if 'png' in linkstr:
                sources.append('https://www.gw-openscience.org'+linkstr)
                descripts.append(str(link.get("title")))
        for link in soup2.find_all("a"):
            linkstr=str(link)
            if 'png' and 'COINC' in linkstr:
                descripts.append(str(link['title']))
                sources.append('https://www.gw-openscience.org'+str(link.get("href")))
                break
        
        for i in range(0,len(sources)):
            lay = GridLayout(rows=2,padding=15)
            filepath = 'Detector_Plot_'+str(i)+'.png'
            os.system("curl -0 "+ sources[i] + ' > ' + filepath)
            img = AsyncImage(source = filepath,size_hint_y=0.8)
            desc = WrapLabel(text=descripts[i],size_hint_y=0.2,color=(0,0,0,1))
            
            obj.add_widget(lay)
            lay.add_widget(img)
            lay.add_widget(desc)
        
        waittime=3600
        i=0
        while i < waittime:
            if main_flag == 1:
                print('plotthread closing...')
                return
            i+=5
            time.sleep(5)

class DetectLabel(ButtonBehavior,Label):
    pass

class StatusScreenv2(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        t = threading.Thread(target=statusupdate,args=(self,),daemon=True)
        t.start()
  
    def retract(self,presser):
        for child in self.children[0].children:
            if child.pos[1] < 240:
                anim = Animation(x=child.pos[0],y=child.pos[1]-240-child.height,duration=0.5)
                anim.start(child)
            elif child.pos[1] > 240:
                anim=Animation(x=child.pos[0],y=240+child.pos[1]+child.height,duration=0.5)
                anim.start(child)
                
        App.get_running_app().root.transition=FadeTransition(duration=0.3)
        def change(dt):
            App.get_running_app().root.current='statinfo'
        Clock.schedule_once(change,0.5)
        
#class StatusScreen(Screen):
#    '''DETECTOR STATUS SCREEN'''
#    def __init__(self,**kwargs):
#        super().__init__(**kwargs)
#        layout = GridLayout(cols=1,rows=2,spacing=30,padding=30, row_default_height=150)
#        with layout.canvas.before:
#            Color(.2,.2,.2,1)
#            self.rect=Rectangle(size=(800,600),pos=layout.pos)
#
#        self.add_widget(layout)
#
#        detLay = BoxLayout(orientation='vertical',spacing=10)
#
#        for i in range(0,4):
#            lay = DetGrid(cols=3,spacing=10,padding=10)
#            for j in range(0,3):
#                box = DetLabel(text='test'+str(j))
#                lay.add_widget(box)
#            with lay.canvas.before:
#                lay.col = Color(1,0,1,0)
#                lay.rect=Rectangle(pos=lay.pos)
#            detLay.add_widget(lay)
#            
#        layout.add_widget(detLay)        
#
#        t = threading.Thread(target=statusupdate,args=(detLay,),daemon=True)
#        t.start()
#
#        button3 = MainButton(text='Main Menu',name='main',size_hint_y=0.25)
#        layout.add_widget(button3)

class StatBio(Screen):
    def change(obj):
        App.get_running_app().root.current = 'status'
        App.get_running_app().root.transition=NoTransition()
        for child in App.get_running_app().root.current_screen.children[0].children:
            if child.pos[1] < 240:
                anim = Animation(x=child.pos[0],y=240+child.pos[1]+child.height)
                anim.start(child)
            elif child.pos[1] > 240:
                anim=Animation(x=child.pos[0],y=child.pos[1]-240-child.height)
                anim.start(child)
        App.get_running_app().root.transition=SlideTransition()
    pass

class PlotsScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout=GridLayout(rows=2)
    
        carousel = Carousel(direction='right',size_hint_y=0.9)
        self.add_widget(layout)
        layout.add_widget(carousel)
        
        t3 = threading.Thread(target=plotupdate,args=(carousel,),daemon=True)
        t3.start()
        
        button4 = MainButton(text='Main Menu',name='main',size_hint_y=0.1)
        layout.add_widget(button4)

class MyApp(App):
    def build_config(self,config):
        config.setdefaults('Section',{'InitialBackup':'0'})
    def on_start(self):
        global flag
        global main_flag
        global newevent_flag
        flag = 0
        main_flag=0
        newevent_flag=0
        
    def build(self):
        config = self.config
        if config.get('Section','InitialBackup') == '0':
            print('Performing Initial Event Sync. Please be patient - this may take a while...')
            sync_database()
            config.set('Section','InitialBackup','1')
            config.write()
            print('Initial Event Sync Complete...')
        elif config.get('Section','InitialBackup') == '1':
            print('Event Sync not required...')
        
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(StatusScreenv2(name='status'))
        sm.add_widget(PlotsScreen(name='plots'))
        sm.add_widget(StatBio(name='statinfo'))
        
        print('Initialising application...')
        return sm

#Spyder test functionality
def reset():
    import kivy.core.window as window
    from kivy.base import EventLoop
    if not EventLoop.event_listeners:
        from kivy.cache import Cache
        window.Window = window.core_select_lib('window', window.window_impl, True)
        Cache.print_usage()
        for cat in Cache._categories:
            Cache._objects[cat] = {}    

if __name__ == '__main__':
    reset()
    MyApp().run()
