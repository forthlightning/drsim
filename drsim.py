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
		# check each appliance instance
		for i in self.appliances:
			# check each start time in array
			for j in i.start_times:
				# is start time scheduled in DR window?
				if (j >= dr_window[0]) and (j <= dr_window[1]):
					# is load DR-able
					if i.DR == 1:
						i.gogogo.interrupt()

class Appliance:
	DR_power = 0
	kWh_per_hour = [0] * 24
	curtailed = [0] * 24

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
		for i in self.start_times:
			if i-prev < self.duration:
				i = prev + self.duration
			print ("AT: %s" % (i))
			prev = i
		print ""

	def operation(self, env, store):
		end_time = 0
		for i in self.start_times:
			gap = i - end_time
			try:
				# wait for time between now and next scheduled event
				if gap <= 0:
					yield env.timeout(0)
				else:
					yield env.timeout(gap)
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
				end_time = env.now

			except simpy.Interrupt as i:
				Appliance.DR_power += self.power
				Appliance.curtailed[env.now] += self.power
				print "%10s %7s %5s %i" % ("DRed:",self.name, "AT: ", env.now)
				# TODO reschedule DRed event
				
def do_simulation(num, Appliance):
	i = 0
	while i < num:

		# header for looks
		now = datetime.datetime.now()
		print ""
		print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		print ("DR SIM #%s START AT %s:%02d:%02d" % (i+1, now.hour, now.minute, now.second))
		print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		print ""

		print "Daily Schedule"
		print "--------------"
		print ""

		# initialize simpy environment
		env = simpy.Environment()
		# store will hold names of unused appliances
		apps = simpy.FilterStore(env)
		# creates HEAD device, which creates all of the appliances
		HEAD = HomeEnergyAutomationDevice(APPLIANCES, env, apps)
		# run simulation for 1 day
		env.run(until=24)

		# assign dr power and power schedule, wait for next iteration
		yield Appliance.DR_power, Appliance.kWh_per_hour, Appliance.curtailed

		# reset for next round
		Appliance.kWh_per_hour = [0] * 24
		Appliance.DR_power = 0
		Appliance.curtailed = [0] * 24
		i += 1

def main(num_sims, inter_frame_delay):

	# make index
	x = range(24)
	# TODO make timesteps finer
	DR_tot = 0

	# make plots non-blocking
	plt.ion()
	# make figure
	fig = plt.figure()

	ax = fig.add_subplot(1, 1, 1)
	kWh_trace, = ax.plot(x,Appliance.kWh_per_hour,'k-') #comma unpacks tuples
	DR_schedule, = ax.plot(x, Appliance.curtailed, 'k--')

	# visualize DR range
	plt.plot((16, 16), (0, 1500), 'r--')
	plt.plot((19, 19), (0, 1500), 'r--')

	plt.title("Appliance Usage, DR: %s"% (DR_tot))
	plt.show()
	# pause for stability
	time.sleep(1)

	# ask for some number of trials, plot each one
	for DR, kWh, DR_sched in do_simulation(num_sims, Appliance):
		# assign new kWh data to axis
		kWh_trace.set_ydata(kWh)
		DR_schedule.set_ydata(DR_sched)
		plt.title("Appliance Usage, DR: %s"% (DR_tot))
		fig.canvas.draw()
		# wait for readability
		time.sleep(inter_frame_delay)
		DR_tot += DR
		print ""
		print "DR Power: ", DR


if __name__ == '__main__':
	main(5, 1)








