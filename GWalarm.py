import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.uix.pagelayout import PageLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty
from kivy.graphics.instructions import Callback
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
import RPi.GPIO as GPIO
from kivy.lang.builder import Builder

from souptest import statusdetect


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
class MainScreen(Screen):
	def __init__(self,**kwargs):
		super(MainScreen,self).__init__(**kwargs)
		layout=GridLayout(cols=2,rows=2,padding=30,spacing=30,row_default_height=150)
		with layout.canvas.before:
			Color(.2,.2,.2,1)
			self.rect=Rectangle(size=(800,600), pos=layout.pos)

		def exit(obj):
			App.get_running_app().stop()

		quitButton=Button(text='Quit')
		quitButton.bind(on_press=exit)

		self.add_widget(layout)
		ids=('history','status')
		texts=('Event History','Detector Status')
		for i in range(0,len(ids)):
			hbut = MainButton(text=texts[i],id=ids[i])
			layout.add_widget(hbut)
		layout.add_widget(quitButton)

class HistoryScreen(Screen):
	def __init__(self,**kwargs):
		super(HistoryScreen,self).__init__(**kwargs)
		button2 =MainButton(text='Main Menu',id='main')
		self.add_widget(button2)

class NestedBox(BoxLayout):
	pass

class DetLabel(Label):
	detname = StringProperty()
	detstat = NumericProperty()
	dettime = StringProperty()

	

class StatusScreen(Screen):
	def __init__(self,**kwargs):
		super(StatusScreen,self).__init__(**kwargs)
		layout = GridLayout(cols=1,rows=2,spacing=30,padding=30,default_row_height=150)
		with layout.canvas.before:
			Color(.2,.2,.2,1)
			self.rect=Rectangle(size=(800,600),pos=layout.pos)
#Clock.schedule_interval(statusdetect,60)

		self.add_widget(layout)

		detLay = NestedBox()

		det1layout = GridLayout(cols=3,spacing=10,padding=10)
		det2layout=GridLayout(cols=3,spacing=10,padding=10)
		det3layout=GridLayout(cols=3,spacing=10,padding=10)

		layout.add_widget(detLay)
		detLay.add_widget(det1layout)
		detLay.add_widget(det2layout)
		detLay.add_widget(det3layout)

		statids = ['test1','test2','test3']

		(detectornames,statuses,detectortimes) = statusdetect(

		button3 = MainButton(text='Main Menu',id='main')
		layout.add_widget(button3)

sm = ScreenManager()
sm.add_widget(MainScreen(name='main'))
sm.add_widget(HistoryScreen(name='history'))
sm.add_widget(StatusScreen(name='status'))

class MyApp(App):
	def build(self):
		return sm

if __name__ == '__main__':
	MyApp().run()
