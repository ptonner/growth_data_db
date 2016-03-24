import time, datetime
import pandas as pd


def convert_time(time):
	time = time.apply(_parse_time)
	time = time.apply(_convert_delta_to_hours,args=(time[0],))
	#time = time.round(2)
	return time

def _convert_delta_to_hours(time,t0):
		delta = time - t0
		return 24*delta.days + float(delta.seconds)/3600

def _parse_time(t):
	try:
		return datetime.datetime(*time.struct_time(time.strptime(t,'%H:%M:%S'))[:-2])
	except ValueError, e:
		try:
			t = time.strptime(t,'%d %H:%M:%S')
			t = list(t)
			t[2]+=1
			
			return datetime.datetime(*time.struct_time(t)[:-2])
		except ValueError, e:
			raise Exception("Time format unknown")
