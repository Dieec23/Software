
import math
import json

def kahan_range(start, stop, step):
  assert step > 0.0
  total = start
  compo = 0.0
  while total < stop:
    yield total
    y = step - compo
    temp = total + y
    compo = (temp - total) - y
    total = temp


numberedMode = True      #call data[0] vs data[time] for values

json_data = {}
json_data['sample'] = {}
json_data['initialTime'] = '112341'
json_data['sampleRate'] = '.2'
json_data['arrayName'] = '1'

initTime = int(json_data['initialTime'])
curTime = initTime
rate = float(json_data['sampleRate'])
readingNum = 0

for s in kahan_range(0.0, 20.0, rate):
  inches = format(12*abs(math.sin(math.pi*s/21))*12, '.2f')
  temp = format(68+abs(math.sin(math.pi*s/13))*31, '.2f')
  data ={}
  if numberedMode:
    data['time'] = format(curTime)
    data['dist'] = inches
    data['temp'] = temp
    json_data['sample'][format(readingNum)] = data
  else :
    json_data['sample'][format(curTime)] ={}
    json_data['sample'][format(curTime)]['dist'] = inches
    json_data['sample'][format(curTime)]['temp'] = temp
  curTime += rate
  readingNum +=1

print json.dumps(json_data)
  #if 1 : #(inches < '61.0') and (temp > '90.0') :
   # print 'Time({}): Dist: {} in, Temp: {} deg F'.format(s,inches,temp,)
