def statusdetect():

	from bs4 import BeautifulSoup 
	import requests 
	import re

	url = "https://ldas-jobs.ligo.caltech.edu/~gwistat/gwistat/gwistat.html"
	r =requests.get(url) 
	soup = BeautifulSoup(r.text,"lxml")

	def identifystring(line):
		result = re.search('>(.*)<',str(line))
		return result.group(1)

	detectornames = []
	detectortimes = []

	for row in soup("td"):
		res = identifystring(row)
	
		if len(res) > 20 :
			continue


		for char in res:
			if char == '':
				if once == True:
					res = ''
					break
				once = 1
				continue
			if char == '<':
				res=''
				break
			if char == ':':
				detectortimes.append(res)
				res=''
				break
            
		finalcheck = ['Detector','Status','Duration','']

		if res not in finalcheck:
			detectornames.append(res)

		statuses=[]
		for element in detectornames:
			if element in ['Observing','Science']:
				statuses.append(2)
			elif element == 'Down':
				statuses.append(0)
			else:
				statuses.append(1)

	return detectornames,statuses,detectortimes
#	obj.detectornames=detectornames
#	obj.statuses=statuses,
#	obj.detectortimes=detectortimes
#print(statusdetect())
