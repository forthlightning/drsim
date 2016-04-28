import random as r
import simpy
import pprint as pp

RANDOM_SEED = 12345

WASHER = {'name':'washer','power':1000, 'DR':1, 'lowbound':6, 'highbound':10, 'noevents':1, 'duration':1}
DRYER = {'name':'dryer','power':500, 'DR':1, 'lowbound':12, 'highbound':17, 'noevents':2, 'duration':2}
APPLIANCES = {'washer':WASHER, 'dryer':DRYER}

def make_timeline():
	"""
		this thing should fill up a schedule to later be executed
	"""
	events = []

	for i in APPLIANCES:
		appliance = APPLIANCES[i]
		events_left = appliance['noevents']
		
		while events_left >= 1:

			t_start = random.randint(appliance['lowbound'],appliance['highbound'])
			t_stop = t_start + appliance['duration']

			events.append((appliance['name'],t_start, t_stop, appliance['power'], appliance['DR']))
			events_left -= 1
	# Events have the form (name, start, stop, power, DR)
	schedule = []
	event_set = {''}
	len_set = len(event_set)

	for i in events:
		event_set.add(i[0])
		if len_set != len(event_set):
			sched = [0] * 24
			duration = i[2]-i[1]
			time = i[1]
			while duration >= 1:
				sched[time] = i[3]
				time += 1
				duration -= 1
			schedule.append(sched)
			sched = []
			len_set = len(event_set)

		else:
			time = i[1]
			duration = i[2]-i[1]
			sched = schedule[-1]
			while duration >= 1:
				sched[time] = i[3]
				time += 1
				duration -= 1
			schedule[-1] = sched

	return schedule

class HomeEnergyAutomationDevice:
	def __init__(self, APPLIANCES):
		# receive array of dictionaries APPLIANCES
		# schedule event one for each instance of each appliance
		# schedule DR event

		self.app_dict = APPLIANCES

		# stores inactive appliances
		apps = simpy.FilterStore(env)

		appliances = []
		for i in self.app_dict:

			# add Appliance object to array of appliances
			appliances.append(Appliance(i))

			# add string of appliance name to filterstore
			apps.put(i['name'])


		DR = env.process(self.demand_response(env))

	def demand_response():
	


class Appliance:
	def __init__(self, appliance_info):
		# takes input of appliance info dictionary, allocates parameters appropriately
		self.env = env
		self.power = appliance_info['power']
		self.name = appliance_info['name']
		self.DR = appliance_info['DR']
		self.noevents = appliance_info['noevents']
		self.duration = appliance_info['duration']
		self.lowbound = appliance_info['lowbound']
		self.highbound = appliance_info['highbound']

		# TODO more than one start time?
		self.start_time = r.randint(self.lowbound, self.highbound)

	def operation:
		while True:
			try:
				if apps.get(lambda x: x == self.name):
				yield env.timeout(self.start_time)
				print('appliance %s started at time %i' % (self.name, env.now))

				# add energy use to counter
				kWh_per_hour[env.now] += self.power


			except: simpy.Interrupt as i:
				print "%S DR-ed at %d" % (self.name, env.now)
				




# can schedule events at some later time with env.schedule(event, priority, delay)
# global hourly energy tally
kWh_per_hour = [0] * 24

env = simpy.Environment()

