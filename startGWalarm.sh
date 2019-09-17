#!/bin/bash
#xdotool windowminimize $(xdotool getactivewindow)
echo $(tvservice -s)
state=$(tvservice -s)
state2=${state:6:4}
echo $state2
if [ $state2 == '0x40' ]
	then
	echo HDMI not active
	#export VC_DISPLAY=5
	sed -i -e 's/#//g' ~/.kivy/config.ini
	sudo amixer -c 0 cset numid=3 1
elif [ $state2 == '0x12' ]
	then
	echo HDMI active
	sed -i -e 's/#//g' ~/.kivy/config.ini
	sed -i -e 's/mtdev_%(name)s/#mtdev_%(name)s/g' ~/.kivy/config.ini
	sed -i -e 's/hid_%(name)s/#hid_%(name)s/g' ~/.kivy/config.ini
	sudo amixer -c 0 cset numid=3 2
else
	echo Default configuration settings mouse + keyboard
	sed -i -e 's/#//g' ~/.kivy/config.ini
	sed -i -e 's/mtdev_%(name)s/#mtdev_%(name)s/g' ~/.kivy/config.ini
	sed -i -e 's/hid_%(name)s/#hid_%(name)s/g' ~/.kivy/config.ini
	sudo amixer -c 0 cset numid=3 0
fi
SCRIPTSDIR=/home/pi/Documents/GIT/gwalarm/
sudo -E python3 ${SCRIPTSDIR}GWalarm_screens.py