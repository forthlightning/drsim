import random as r
import simpy
import pprint as pp
import datetime
import numpy as np
from matplotlib import pyplot as plt
import time

WASHER = {'name':'Washer','power':1000, 'DR':1, 'lowbound':6, 'highbound':10, 'noevents':1, 'duration':1}
DRYER = {'name':'Dryer','power':500, 'DR':1, 'lowbound':6, 'highbound':17, 'noevents':3, 'duration':2}
APPLIANCES = {'Washer':WASHER, 'Dryer':DRYER}

class HomeEnergyAutomationDevice:
	def __init__(self, APPLIANCES, env, store):
		# receive array of dictionaries APPLIANCES
		# schedule event one for each instance of each appliance
		# schedule DR event
		self.name = "HEAD"
		self.env = env
		self.app_dict = APPLIANCES
		self.appliances = []
		for i in self.app_dict:
			# add Appliance object to array of appliances
			self.appliances.append(Appliance(self.app_dict[i], env, store))

			# add string of appliance name to filterstore
			store.put(self.app_dict[i]['name'])
		dr_window = (16,19)
		self.DR = env.process(self.demand_response(APPLIANCES, dr_window, store, env))

		#DR = env.process(self.demand_response(env))

	def demand_response(self, APPLIANCES, dr_window, store, env):
		yield env.timeout(dr_window[0])
		for i in self.appliances:
			for j in i.start_times:
				if (j >= dr_window[0]) and (j <= dr_window[1]):
					i.gogogo.interrupt()

class Appliance:
	DR_power = 0
	kWh_per_hour = [0] * 24

	def __init__(self, appliance_info, env, store):
		# takes input of appliance info dictionary, allocates parameters appropriately
		self.env = env
		self.power = appliance_info['power']
		self.name = appliance_info['name']
		self.DR = appliance_info['DR']
		self.noevents = appliance_info['noevents']
		self.duration = appliance_info['duration']
		self.lowbound = appliance_info['lowbound']
		self.highbound = appliance_info['highbound']

		inter = np.linspace(self.lowbound, self.highbound, self.noevents+1)
		intervals = []
		for i in inter:
			intervals.append(int(i))

		self.start_times = []

		for first, second in zip(intervals, intervals[1:]):
			self.start_times.append(r.randint(first,second))

		self.gogogo = env.process(self.operation(env, store))
		print "%s %s Event(s)" % (len(self.start_times), self.name)
		prev = 0
		print "start times ", self.start_times
		for i in self.start_times:
			if i-prev < self.duration:
				i = prev + self.duration
			print ("AT: %s" % (i))
			prev = i
		print ""

	def operation(self, env, store):
		for i in self.start_times:
			prev = 0
			gap = i - prev
			try:
				# wait until start time
				yield env.timeout(gap)
				prev = i
				#print "Store has: ", store.items
				#print "I am %s" % self.name

				# pull appliance from store, start using power
				yield store.get(lambda x: x == self.name)

				duration = self.duration
				print('%10s %7s %5s %i' % ("STARTED:",self.name,"AT: ", env.now))
				while duration > 0:
					Appliance.kWh_per_hour[env.now] += self.power
					yield env.timeout(1)
					duration -= 1

				yield store.put(self.name)
				print "%10s %7s %5s %i" % ("FINISHED:",self.name, "AT: ", env.now)

			except simpy.Interrupt as i:
				Appliance.DR_power += self.power
				print "%10s %7s %5s %i" % ("DRed:",self.name, "AT: ", env.now)
				
def do_simulation(num, Appliance):
	i = 0
	while i < num:

		# header for looks
		now = datetime.datetime.now()
		print ""
		print ("~~~~~~~~~~~~~~~~~~~~~")
		print ("DR SIM #%s START AT %s:%02d:%02d" % (i+1, now.hour, now.minute, now.second))
		print ("~~~~~~~~~~~~~~~~~~~~~")
		print ""

		print "Daily Schedule"
		print "______________"
		print ""

		env = simpy.Environment()
		apps = simpy.FilterStore(env)
		HEAD = HomeEnergyAutomationDevice(APPLIANCES, env, apps)

		# run simulation for 1 day
		env.run(until=24)


		yield Appliance.DR_power, Appliance.kWh_per_hour

		# reset for next round
		Appliance.kWh_per_hour = [0] * 24
		Appliance.DR_power=0
		i += 1

def main():

	# make index
	x = range(24)

	# make figure
	plt.ion()
	fig = plt.figure()

	ax = fig.add_subplot(1, 1, 1)
	par_plot, = ax.plot(x,Appliance.kWh_per_hour,'k-')

	plt.plot((16, 16), (0, 1000), 'r--')
	plt.plot((19, 19), (0, 1000), 'r--')
	plt.title("Appliance Usage")
	plt.show()
	# wait for stability
	time.sleep(.1)


	#axes(ax) # selects current axis as active

	for DR, kWh in do_simulation(5, Appliance):
		par_plot.set_ydata(kWh)
		fig.canvas.draw()
		# wait for readability
		time.sleep(1)
		print "DR Power: ", DR








if __name__ == '__main__':
	main()








