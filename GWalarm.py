import kivy
kivy.require('1.11.0')

import threading
import time
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.uix.pagelayout import PageLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.graphics.instructions import Callback
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup
from kivy.uix.behaviors  import ButtonBehavior

#import RPi.GPIO as GPIO
from kivy.lang.builder import Builder

from souptest import statusdetect
import gcn
from gcn_test import process_gcn
import requests
from bs4 import BeautifulSoup
from tables import * 
import datetime
import os

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

#FIXME: DECLARE ALL GPIO PINS AND INITIAL INS/OUTS HERE



Builder.load_file('GWalarm.kv',rulesonly=True)

class MainButton(Button):
    def nav(self):
        app=App.get_running_app()
        if self.id=='history':
            app.root.current='history'
        elif self.id=='status':
            app.root.current='status'
        elif self.id=='main':
            app.root.current='main'
        elif self.id=='plots':
            app.root.current='plots'
class MainScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout=GridLayout(cols=2,rows=2,padding=30,spacing=30,row_default_height=150)
        with layout.canvas.before:
            Color(.2,.2,.2,1)
            self.rect=Rectangle(size=(800,600), pos=layout.pos)
            
        def exit(obj):
            App.get_running_app().stop()
        quitButton=Button(text='Quit')
        quitButton.bind(on_press=exit)

        self.add_widget(layout)
        ids=('history','status','plots')
        texts=('Event History','Detector Status','Test Plots')
        [layout.add_widget(MainButton(text=texts[i],id=ids[i])) for i in range(0,len(ids))]
#            hbut = MainButton(text=texts[i],id=ids[i])
#            layout.add_widget(hbut)
        layout.add_widget(quitButton)

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
                
        h5file = open_file("Event Database",mode="a",title="eventinfo")
        try:
            h5file.create_group("/",'events')
        except NodeError:
            pass
        
        
        #grab a table, it doesn't matter which one!
        x=0
        for table in h5file.iter_nodes(where="/events",classname="Table"):
            tables=table
            if x==0:
                break
        
        def receive():
                gcn.listen(host="209.208.78.170",handler=process_gcn)
        t4 = threading.Thread(target=receive,daemon=True)
        t4.start()
            
        
#        if 'tables' in locals():
        names = tables.colnames
        nameLay = GridLayout(cols=len(names),size_hint_y=0.2)
        specialnames=['GraceID','Instruments','FAR','DetectionTime','UpdateTime']
        for name in specialnames:
            lab = WrapLabel(text=name)
            nameLay.add_widget(lab)
        layout.add_widget(nameLay)
        hisScroll = ScrollView(do_scroll_x=False,size_hint=(1,1))
        layout.add_widget(hisScroll)
    
        hisBox = BoxLayout(orientation='vertical',size_hint_y=None,height=1000)
        hisScroll.add_widget(hisBox)

        t2 = threading.Thread(target=historyUpdate,args=(hisBox,names,specialnames),daemon=True)
        t2.start()
#        else:
#            lab = WrapLabel(text='No events to be listed here')
#            layout.add_widget(lab)
        button2 =MainButton(text='Main Menu',id='main',size_hint_y=0.1)
        layout.add_widget(button2)

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

class NestedBox(BoxLayout):
	pass

class PressableLabel(Label):
    pass

class EventContainer(ButtonBehavior,GridLayout):
    namelist=ListProperty(None)
    row = ListProperty(None)
    def details(self):
        #print(self.names)
        #specialnames=['AlertType',']
        
        content=Carousel()
        img = self.row[self.namelist.index('GraceID')]+'.png'
        content.add_widget(AsyncImage(source=img))
        testbut = Button(text='get me out')
        content.add_widget(testbut)
        infoPopup = Popup(title="Superevent Information", content=content,size_hint=(0.8,0.8))
        testbut.bind(on_press=infoPopup.dismiss)
        
        infoPopup.open()
        
def historyUpdate(obj,names,specialnames):
    if os.path.basename(os.getcwd()) != "event_data":
        try:
            os.chdir("./event_data")
        except:
            os.mkdir("./event_data")
            os.chdir("./event_data")
        
    #initial check to ensure file exists with necessary groupings
    h5file = open_file("Event Database",mode="a",title="eventinfo")
    try:
        h5file.create_group("/","events")
    except NodeError:
        pass
    
    h5file.close()
    obj.clear_widgets()
    while True:
        h5file = open_file("Event Database",mode="a",title="eventinfo")
        #get all them tables
        totalno=len(h5file.list_nodes(where="/events",classname="Table"))
        tables = [table for table in h5file.iter_nodes(where="/events",classname="Table")]
        j=0
        for table in tables:
            #read in the last row (most up to date)
            #names = table.colnames
            row = table[-1]
            grid = EventContainer(cols=len(row))
            grid.namelist=names
            orderedrow = []
            for key in names:
                orderedrow.append(row[key].decode())
            grid.row=orderedrow
            specialnames=['GraceID','Instruments','FAR','DetectionTime','UpdateTime']
            for string in row[specialnames]:
                #FIXME: ADD NEAT TEXT BY PARSING INPUT TEXT
                decoded = string.decode()
                if decoded == '':
                    decoded = row['UpdateTime'].decode()
                lab = Label(text=decoded,color=(0,0,0,1))
                grid.add_widget(lab)
                #output_info[names[i]] = decoded
            #for key, item in output_info.items():
             #   lab = WrapLabel(text=key+' : '+item)
              #  grid.add_widget(lab)
            obj.add_widget(grid,index=totalno-j)
            j+=1
        
        h5file.close()
        time.sleep(60)
        
def statusupdate(obj):
    while True:
        (detnames,stats,dettimes) = statusdetect()
        
        names = ['GEO 600', 'LIGO Hanford', 'LIGO Livingston','Virgo']
        order = [dettimes,detnames,names]
        j=0
        for child in obj.children:
            if stats[j] != 2:
                child.current_color=[1-stats[j],0,stats[j],1]
            else:
                child.current_color=[0,1,0,1]
            with child.canvas:
                    Color(rgba=child.current_color)
            i=0
            for label in child.children:
                label.text=order[i][j]
                i+=1
            j+=1
            
        time.sleep(30)

def plotupdate(obj):
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
        
        #grab the soup and parse for links + descripts
        try:
            resp=requests.get(url)
            r = resp.text
            soup=BeautifulSoup(r,"lxml")
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

        for i in range(0,len(sources)):
            lay = GridLayout(rows=2,padding=15)
            filepath = 'Detector_Plot_'+str(i)+'.png'
            os.system("curl -0 "+ sources[i] + ' > ' + filepath)
            img = AsyncImage(source = filepath,size_hint_y=0.8)
            desc = WrapLabel(text=descripts[i])
            
            obj.add_widget(lay)
            lay.add_widget(img)
            lay.add_widget(desc)
            
        #j=0
        #for source in sources:
        #    os.system("curl -0 "+ source + ' > ' + filepaths[j])
        #    j+=1

        time.sleep(3600)
        
class StatusScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(cols=1,rows=2,spacing=30,padding=30, row_default_height=150)
        with layout.canvas.before:
            Color(.2,.2,.2,1)
            self.rect=Rectangle(size=(800,600),pos=layout.pos)

        self.add_widget(layout)

        detLay = NestedBox()

        for i in range(0,4):
            lay = DetGrid(cols=3,spacing=10,padding=10)
            for j in range(0,3):
                box = DetLabel(text='test'+str(j))
                lay.add_widget(box)
            with lay.canvas.before:
                lay.col = Color(1,0,1,0)
                lay.rect=Rectangle(pos=lay.pos)
            detLay.add_widget(lay)
            
        layout.add_widget(detLay)        

        t = threading.Thread(target=statusupdate,args=(detLay,),daemon=True)
        t.start()

        button3 = MainButton(text='Main Menu',id='main',size_hint_y=0.25)
        layout.add_widget(button3)

class PlotsScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout=GridLayout(rows=2)
    
        carousel = Carousel(direction='right',size_hint_y=0.9)
        #layout2=GridLayout(rows=2)
        
        self.add_widget(layout)
        layout.add_widget(carousel)
        #carousel.add_widget(layout2)
        
#        current_plot = Image(source='./event_data/Detector_Plot_0.png')
#        current_desc = Label(text='Nothing yet...',size_hint_y=None,height=75)
#        
#        layout2.add_widget(current_plot)
#        layout2.add_widget(current_desc)
#        
        t3 = threading.Thread(target=plotupdate,args=(carousel,),daemon=True)
        t3.start()
        
        button4 = MainButton(text='Main Menu',id='main',size_hint_y=0.1)
        layout.add_widget(button4)

sm = ScreenManager()
sm.add_widget(MainScreen(name='main'))
sm.add_widget(HistoryScreen(name='history'))
sm.add_widget(StatusScreen(name='status'))
sm.add_widget(PlotsScreen(name='plots'))

class MyApp(App):
#    def on_start(self):

        
    def build(self):
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
