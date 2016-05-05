import random as r
import simpy
import pprint as pp
import datetime
import numpy as np
from matplotlib import pyplot as plt
import time

r.seed(12345)

WASHER = {'name':'Washer','power':1000, 'DR':1, 'lowbound':6, 'highbound':10, 'noevents':1, 'duration':1}
DRYER = {'name':'Dryer','power':500, 'DR':1, 'lowbound':6, 'highbound':17, 'noevents':2, 'duration':2}
HEATER = {'name':'Heater','power':100, 'DR':1, 'lowbound':0, 'highbound':20, 'noevents':7, 'duration':2}
APPLIANCES = {'Washer':WASHER, 'Dryer':DRYER, 'Heater':HEATER}
TOU = [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 22, 22, 34, 34, 34, 34, 34, 34, 22, 22, 15, 15, 15] 
class HomeEnergyAutomationDevice:
	def __init__(self, APPLIANCES, env, store):
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
		self.on_off = 0

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
				# if gap is < 1, proceed without waiting
				if gap <= 0:
					yield env.timeout(0)
				# if not, wait an appropriate amount of time
				else:
					yield env.timeout(gap)

				# pull appliance from store, start using power
				yield store.get(lambda x: x == self.name)

				duration = self.duration
				print('%10s %7s %5s %i' % ("STARTED:",self.name,"AT: ", env.now))
				while duration > 0:
					self.on_off = 1
					Appliance.kWh_per_hour[env.now] += self.power
					yield env.timeout(1)
					duration -= 1

				yield store.put(self.name)
				print "%10s %7s %5s %i" % ("FINISHED:",self.name, "AT: ", env.now)
				end_time = env.now
				self.on_off = 0

			except simpy.Interrupt as i:
				Appliance.DR_power += self.power
				Appliance.curtailed[env.now] += self.power
				store.put(self.name)
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

		# return DR_power for run i, as well as scheduled demand and curtailed demand
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


	# make plots non-blocking
	plt.ion()

	# make figure
	fig = plt.figure()

	# first graph
	ax = fig.add_subplot(3, 1, 1)

	# visualize DR range
	plt.plot((16, 16), (0, 1500), 'r--')
	plt.plot((19, 19), (0, 1500), 'r--')

	# dynamic title
	plt.title("Appliance Usage")

	# live update graph
	x2 = range(num_sims)

	cum_energy_series = [0] * num_sims
	ax2 = fig.add_subplot(3, 1, 2)
	cum_energy_trace, = ax2.plot(x2,cum_energy_series)
	cum_energy_money = 0

	DR_series = [0] * num_sims
	ax3 = fig.add_subplot(3, 1, 3)
	DR_trace, = ax3.plot(x2, DR_series)
	DR_money_tot = 0

	plt.show()


	# pause for stability
	time.sleep(1)

	trial = 0

	# ask for some number of trials, plot each one
	for DR_watts, watt_schedule, DR_sched in do_simulation(num_sims, Appliance):

		# generate two sets of bars, one for demand, one for curtailed demand
		power_usage = ax.bar(x, watt_schedule, 1)
		curtailed_schedule = ax.bar(x, DR_sched, 1)

		# cycle through each timestep
		for i in range(len(watt_schedule)):
			# update bar lengths
			power_usage[i].set_height(watt_schedule[i])
			curtailed_schedule[i].set_height(DR_sched[i])
			# power gets plotted in blue, DR gets plotted in red
			if watt_schedule[i] != 0:
				power_usage[i].set_color('b')
			elif DR_sched[i] != 0:
				curtailed_schedule[i].set_color('r')
			else:
				pass		

		# pause for trippy visuals
		time.sleep(inter_frame_delay)

		energy_money = 0
		for hourly, price in zip(watt_schedule, TOU):
			# .001 is kwh per watt hour
			energy_money += hourly * (.001) * price

		cum_energy_money += energy_money/100
		cum_energy_series[trial] = cum_energy_money
		cum_energy_trace.set_xdata(x[:len(cum_energy_series)])
		cum_energy_trace.set_ydata(cum_energy_series)
		ax2.set_ylim([0,max(cum_energy_series)])

		DR_money = 0
		for curtail, price in zip(DR_sched, TOU):
			DR_money += curtail * price * .001
			print DR_money

		DR_money_tot += DR_money/100
		print DR_money_tot
		DR_series[trial] = DR_money_tot
		DR_trace.set_xdata(x[:len(DR_series)])
		print DR_series
		DR_trace.set_ydata(DR_series)
		ax3.set_ylim([0,DR_money_tot])

		trial += 1

		# re-draw figure
		fig.canvas.draw()

		# reset graph for next run
		print ""
		print "DR Power: ", DR_watts
		for i in range(len(watt_schedule)):
			power_usage[i].set_height(0)
			curtailed_schedule[i].set_height(0)	


		
		print "energy money", energy_money/100


if __name__ == '__main__':
	main(10, .5)








