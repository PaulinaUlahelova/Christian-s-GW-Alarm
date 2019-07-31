import kivy
kivy.require('1.11.0')

import threading
import time
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
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
from kivy.uix.scatter import Scatter

#import RPi.GPIO as GPIO
from kivy.lang.builder import Builder

from souptest import statusdetect
import requests
from bs4 import BeautifulSoup
from tables import * 
import datetime
import os

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
		for i in range(0,len(ids)):
			hbut = MainButton(text=texts[i],id=ids[i])
			layout.add_widget(hbut)

		layout.add_widget(quitButton)

class HistoryScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(rows=2)
        self.add_widget(layout)
        hisScroll = ScrollView(do_scroll_x=False,size_hint=(1,None))
        layout.add_widget(hisScroll)
        button2 =MainButton(text='Main Menu',id='main')
        hisScroll.add_widget(button2)
#        
#        t2 = threading.Thread(target=historyUpdate,args=(HistoryScreen,),daemon=True)
#        t2.start()
#    
    
class DetGrid(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
            
class DetLabel(Label):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color([0,0,0,0])
        

class NestedBox(BoxLayout):
	pass

def historyUpdate(obj):
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
    
    while True:
        h5file = open_file("Event Database",mode="a",title="eventinfo")
#       
        
        
        h5file.close()
        
        time.sleep(60)
        
        

def statusupdate(obj):
    while True:
        (detnames,stats,dettimes) = statusdetect()
        
        names = ['GEO 600', 'LIGO Hanford', 'LIGO Livingston']
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
    
        time.sleep(30)#

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
        
        #grab the soup and pzrse for links + descripts
        resp=requests.get(url)
        r = resp.text
        soup=BeautifulSoup(r,"lxml")
        
        sources=[]
        descripts=[]
        for link in soup.find_all("a"):
            linkstr = str(link.get("href"))
            if 'png' in linkstr:
                sources.append('https://www.gw-openscience.org'+linkstr)
                descripts.append(str(link.get("title")))
        filepaths =[]
        for i in range(0,len(sources)):
            filepaths.append('Detector_Plot_'+str(i)+'.png')
        j=0
        for source in sources:
            os.system("curl -0 "+ source + ' > ' + filepaths[j])
            j+=1
            
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

        for i in range(0,3):
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

        button3 = MainButton(text='Main Menu',id='main')
        layout.add_widget(button3)

class PlotsScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout=GridLayout(rows=2)
        layout2=GridLayout(rows=2)
        
        self.add_widget(layout)
        layout.add_widget(layout2)
        
        plot_handle = Scatter(do_rotation=False,do_translation=False,scale_min=3,scale_max=10)
        current_plot = Image(size=(800,600),source='./event_data/Detector_Plot_0.png')
        current_desc = Label(text='Nothing yet...')
        
        layout2.add_widget(plot_handle)
        plot_handle.add_widget(current_plot)
        layout2.add_widget(current_desc)
        
        t3 = threading.Thread(target=plotupdate,args=(layout,),daemon=True)
        t3.start()
        
        
        
        button4 = MainButton(text='Main Menu',id='main',size_hint_y=None,height=25)
        layout.add_widget(button4)

sm = ScreenManager()
sm.add_widget(MainScreen(name='main'))
sm.add_widget(HistoryScreen(name='history'))
sm.add_widget(StatusScreen(name='status'))
sm.add_widget(PlotsScreen(name='plots'))

class MyApp(App):
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
