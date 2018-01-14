import os
import shutil
import datetime
import time
import pickle
from random import randint

import extract_data

VERSION = 1

LONG_WAIT = 20

USER_EXTRACT_ITEMS = {'enabled', 'name', 'altname', 'username', 'intro', 'cities', 'work', 'edu', 'romantic', 'contact', 'basic', 'details', 'milestones', 'family', 'possfam', 'friends', 'quotes', 'groups'}
GROUP_EXTRACT_ITEMS = {'url', 'name', 'size', 'about', 'admins', 'members'}

# dictionary whose keys are datetime objects
# used to track the history of values of a variable
# update function compares with most recent instance. Adds new key-value pair only when value has changed
class dated_dict(dict):

	# when full_history == True, it keeps all values with their date-stamps
	# when full_history == False, it keeps a list of values and only the date of the most-recent update
	def __init__(self, value = None, full_history = True):
		if type(full_history) != bool:
			raise Exception("full_history must be assigned a boolean value")
		if full_history == False and value != None and type(value) != list:
			raise Exception("value should be of type list when full_history = False")

		self._hist = full_history
		today = datetime.date.today()
		self._date = today
		if value != None or full_history == True:
			self[today] = value
		else:
			self[today] = []

	# most recent date that a value was passed to the object
	def date(self):
		return self._date

	# most recent date that a "new" value was passed to the object
	def keydate(self):
		return max(list(self.keys()))

	# returns list of all current and past values
	# if each value is itself a list then it concatenates these lists
	def all(self):
		type_list = True
		for v in self.values():
			if v != None and type(v) != list:
				type_list = False
		if type_list:
			l = []
			for v in self.values():
				if v != None:
					for i in v:
						l.append(i)
			return l
		return list(self.values())

	# passes value to object
	# if the value is different from the most recent, the dictionary will be updated with today's date as new key
	# if the value is the same as the most recent, only self._date is updated to today's date
	def update(self, value):
		today = datetime.date.today()
		self._date = today
		if value == self():
			return
		if self._hist == True:
			self[today] = value
		else:
			if type(value) != list:
				raise Exception("value should be of type list when _hist = False")
			old = self()
			for i in old:
				if i not in value:
					value.append(i)
			self.pop(self.keydate())
			self[today] = value

	# calling object as function returns most recent value
	def __call__(self):
		return self[self.keydate()]

class facebook_user:

	# creates new instance of facebook_user class
	# input user's profile_id, username, and name
	# monitor = True if program should collect/maintain additional data on account
	# monitor should be set to False for accounts of friends and family. May later be set to True if there is reason.
	def __init__(self, profile_id, monitor, username = None, name = None):

		if type(profile_id) != str or profile_id.isdigit() == False:
			raise Exception("Incorrect argument given for profile_id")
		if type(monitor) != bool:
			raise Exception("monitor must of Boolean type")
		if username != None and type(username) != str:
			raise Exception("username must be a string")
		if name != None and type(name) != str:
			raise Exception("name must be a string")

		self.id = profile_id
		self.username = dated_dict(username)
		self.name = dated_dict(name)
		self.monitor = False

		# lists of instances of facebook_user / facebook_group
		self.rev_friends = [] # people who list user as friend
		self.rev_family = [] # people who list user as family
		self.rev_possfam = [] # people who list user as friend and have same last name
		self.rev_groups = [] # groups that list user as member

		self.set_monitor(monitor)

	def __repr__(self):
		if self.name() != None:
			my_rep = 'facebook_user(' + self.id + ', ' + self.name() + ')'
		else:
			my_rep = 'facebook_user(' + self.id + ')'
		return my_rep

	# called by print and string commands
	# a one-line summary of who the user / account is
	def __str__(self, show_monitor=True):
		if self.username() != None and self.name() != None:
			end = ":" + self.username() + ": " + self.name()
		else:
			end = ''
		if show_monitor:
			return str(self.monitor) + ":" + self.id + end
		else:
			return self.id + ":" + end

	# set the value of the monitor attribute
	def set_monitor(self, monitor):
		if self.monitor == monitor:
			return

		self.monitor = monitor
		if monitor == False:
			return

		self.enabled = dated_dict() # True if FB account is enabled. False if FB account is (possibly temporarily) disabled

		self.altname = dated_dict() # Optional alternate name listed beneath their name at bottom of their cover photo
		self.intro = dated_dict() # intro section on their main page
		self.cities = dated_dict() # cities they list having lived in
		self.work = dated_dict() # work they list
		self.edu = dated_dict() # education they list
		self.romantic = dated_dict() # relationship status listed
		self.contact = dated_dict() # contact info listed
		self.basic = dated_dict() # basic info listed (i.e. political views, religion, languages, gender)
		self.details = dated_dict() # details they list about themself on about page
		self.milestones = dated_dict() # the timeline of key events listed on their about page

		# list of dictionaries with keys 'name', 'relation' and when available 'id', 'username'
		self.family = dated_dict(full_history=False) # lists family members on Facebook as instances of facebook_user
		self.family_details = dated_dict(full_history=False) # lists all family members, both on and off Facebook, together with relation

		# list of instances of facebook classes
		self.possfam = dated_dict(full_history=False) # friends they list who have same last name
		self.friends = dated_dict(full_history=False) # friends they list
		self.followers = dated_dict(full_history=False) # Not functioning yet
		self.following = dated_dict(full_history=False) # Not functioning yet
		self.groups = dated_dict(full_history=False) # FB groups they are a member of
		self.events = dated_dict(full_history=False) # Not functioning yet
		self.likes = dated_dict(full_history=False) # Not functioning yet


		self.checkins = dated_dict(full_history=False) # Not functioning yet
		self.reviews = dated_dict(full_history=False) # Not functioning yet
		self.quotes = dated_dict(full_history=False) # quotes they list on their about page

	# returns all known friends as list of instances of facebook_user class
	# uses both rev_friends and friends for optimal results
	def all_friends(self):
		if 'friends' in dir(self):
			myf = self.friends()
			if myf == None or myf == []:
				return self.rev_friends
			return list(set(self.rev_friends) | set(myf))
		else:
			return self.rev_friends

	# returns all family as list
	# uses both rev_family and family for optimal results
	# when facebook_only == True, list items are instances of facebook_user class
	# otherwise, list items are dictionaries
	def all_family(self, facebook_only=True):
		if 'family' in dir(self):
			myf = self.family()
			if myf == None or myf == []:
				fb = self.rev_family
			fb = list(set(self.rev_family) | set(myf))
		else:
			fb = self.rev_family

		if facebook_only:
			return fb

		det = self.family_details()
		for u in fb:
			in_det = False
			for p in det:
				if 'id' in p.keys() and p['id'] == u.id:
					in_det = True
			if in_det == False:
				det.append({'id' : u.id, 'name' : u.name(), 'username' : u.username()})
		return det

	# returns all possible family as list of instances of facebook_user class
	# uses both rev_possfam and possfam for optimal results
	def all_possfam(self):
		if 'possfam' in dir(self):
			mypf = self.possfam()
			if mypf == None or mypf == []:
				return self.rev_possfam
			return list(set(self.rev_possfam) | set(mypf))
		else:
			return self.rev_possfam

	# returns all groups as list of instances of facebook_group class
	# uses both rev_groups and groups for optimal results
	def all_groups(self):
		if 'groups' in dir(self):
			myg = self.groups()
			if myg == None or myg == []:
				return self.rev_groups
			return list(set(self.rev_groups) | set(myg))
		else:
			return self.rev_groups

	# returns a list of all known friends that are monitored
	# list items are instances of facebook_user class
	def monitored_friends(self):
		l = [v for v in self.all_friends() if v.monitor]
		return l

	# returns a list of all known family that are monitored
	# list items are instances of facebook_user class
	def monitored_family(self):
		l = [v for v in self.all_family() if v.monitor]
		return l

	# returns a list of all known possible family that are monitored
	# list items are instances of facebook_user class
	def monitored_possfam(self):
		l = [v for v in self.all_possfam() if v.monitor]
		return l

	# returns a list of all groups that are monitored
	# list items are instances of facebook_group class
	def monitored_groups(self):
		l = [g for g in self.all_groups() if g.monitor]
		return l

	# prints a brief summary of user's info
	def summary(self):
		print(self)

		listed = set()
		not_listed = set()
		not_ext = set()

		for item in {'cities', 'work', 'edu', 'family', 'possfam', 'friends', 'groups'}:
			if item in dir(self) and self.__dict__[item]() != None:
				if self.__dict__[item]() != []:
					listed.add(item)
				else:
					not_listed.add(item)
			else:
				not_ext.add(item)

		extracted = True
		if len(listed.difference({'friends', 'groups'})) > 0:
			print("Lists: " + str(listed.difference({'friends', 'groups'})))
		else:
			if 'enabled' not in dir(self) or True not in self.enabled.values():
				print("Never successfully extracted data for user")
				extracted = False
		if len(not_listed) > 0 and extracted:
			print("Not listed: " + str(not_listed))
		if len(not_ext) > 0 and extracted:
			print("Not extracted: " + str(not_ext))

		if 'friends' in listed:
			print("Friends: " + str(len(self.all_friends())) + ", monitored: " + str(len(self.monitored_friends())))
		else:
			print("Monitored friends: " + str(len(self.monitored_friends())))
		famc = len(self.monitored_family())
		if famc > 0:
			print("Monitored family: " + str(famc))
		pfc = len(self.monitored_possfam())
		if pfc > 0:
			print("Monitored possible family: " + str(pfc))
		if 'groups' in listed:
			print("Groups: " + str(len(self.all_groups())) + ", monitored: " + str(len(self.monitored_groups())))
		else:
			print("Monitored groups: " + str(len(self.monitored_groups())))

	# prints all known monitored connections of user,
	# up to display_bound many items
	# display_bound may be set equal to None
	def print_connections(self, display_bound=25):
		print(self)

		keylist = ['family', 'possfam', 'friends', 'groups']
		items = {
			'family' : self.monitored_family(),
			'possfam' : self.monitored_possfam(),
			'friends' : self.monitored_friends(),
			'groups' : self.monitored_groups()
			}

		if display_bound == None:
			display_bound = max({len(v) for v in items.values()})

		for k in keylist:
			v = items[k]
			if len(v) > 0:
				if len(v) <= display_bound:
					print('------ Monitored ' + k + ' ------')
					for x in v:
						print(x.__str__(False))
				else:
					print('Monitored ' + k + ' count: ' + str(len(v)))

class facebook_group:

	# creates new instance of facebook_group class
	# input group's id, url abbreviation, name, and size
	# monitor = True if program should collect/maintain additional data on group
	# monitor should be set to False for random groups that users subscribe to. May later be set to True if there is reason.
	def __init__(self, group_id, monitor, group_url = None, name = None, size = None):
		if type(group_id) != str or group_id.isdigit() == False:
			raise Exception("Incorrect argument given for group_id")
		if type(monitor) != bool:
			raise Exception("monitor must of Boolean type")
		if group_url != None and type(group_url) != str:
			raise Exception("group_url must be a string")
		if name != None and type(name) != str:
			raise Exception("name must be a string")
		if size != None and type(size) != int:
			raise Exception("size must be an integer")

		self.id = group_id
		self.monitor = False
		self.url = dated_dict(group_url)
		self.name = dated_dict(name)
		self.size = dated_dict(size)

		# list of instances of facebook_user
		self.rev_members = [] # people who have this group in their groups list

		self.set_monitor(monitor)

	def __repr__(self):
		if self.name() != None:
			name = str(self.name().encode('ascii', 'ignore'))[2:-1]
			my_rep = 'facebook_group(' + self.id + ', ' + name + ')'
		else:
			my_rep = 'facebook_group(' + self.id + ')'
		return my_rep

	# called by print and string commands
	# a one-line summary of what the group is
	def __str__(self, show_monitor=True):
		if self.name() != None:
			name = ": " + (str(self.name().encode('ascii', 'ignore'))[2:-1])
		else:
			name = ''
		if self.url() != None and self.url().isdigit() == False:
			url = ":" + self.url()
		else:
			url = ''
		if show_monitor:
			return str(self.monitor) + ":" + self.id + url + name
		else:
			return self.id + url + name

	# set the value of the monitor attribute
	def set_monitor(self, monitor):
		if self.monitor == monitor:
			return
		self.monitor = monitor

		if self.monitor == False:
			return

		self.about = dated_dict()

		# lists of instances of facebook_user class
		self.admins = dated_dict(full_history = False)
		self.members = dated_dict(full_history = False)

		# lists info on when people were added to the group, who added them, etc
		self.member_details = {}

	# returns all known members of group as list of instances of facebook_user class
	# uses rev_members and members for optimal results
	def all_members(self):
		if 'members' not in dir(self):
			return self.rev_members
		mymem = self.members()
		if mymem == None or mymem == []:
			return self.rev_members
		allmem = set(self.rev_members) | set(mymem)
		return list(allmem)

	# returns all members that are monitored as list
	# list items are instances of facebook_user class
	def monitored_members(self):
		l = [u for u in self.all_members() if u.monitor]
		return l

	# returns boolean value indicating if all members are monitored
	def members_are_monitored(self):
		allmon = True
		for u in self.all_members():
			if u.monitor == False:
				allmon = False
		return allmon

	# prints a brief summary of group's info
	def summary(self):
		print(self)
		if self.size() != None:
			print("Size: " + str(self.size()))
		else:
			print("Group size has not been extracted")

		if self.monitor:
			if self.members() == None or self.members() == []:
				print("Group members have not been extracted")
				print("Reverse members: " + str(len(self.rev_members)))
			else:
				print("Monitored members: " + str(len(self.monitored_members())))
		else:
			print("Reverse members: " + str(len(self.rev_members)))
		mon = self.members_are_monitored()
		print("All members monitored: " + str(mon))

	# prints all known monitored connections of group,
	# up to display_bound
	# display_bound may be set to None
	def print_connections(self, display_bound=50):
		print(self)

		mm = self.monitored_members()
		if display_bound == None:
			display_bound = len(mm)

		if len(mm) <= display_bound:
			print("------ Monitored members ------")
			for u in mm:
				print(u.__str__(False))
		else:
			print("Monitored member count: " + str(len(mm)))

class facebook_database:

	# creates new instance of facebook_database class
	# file_name is the file name for saving the database
	def __init__(self, file_name=None):
		self.users = {} # dictionary where keys are user_id numbers and values are facebook_user objects
		self.groups = {} # dictionary where keys are group_id numbers and values are facebook_group objects
		self.file = file_name
		self.version = VERSION

	def __repr__(self):
		if self.file != None:
			return "facebook_database(" + self.file + ".pkl, version " + str(self.version) + ")"
		else:
			return "unsaved facebook_database"

	# called by print and string commands
	# a one-line summary of what the database is
	def __str__(self):
		size = str(len(self.users)) + " users, " + str(len(self.groups)) + " groups"
		if self.file != None:
			return self.file + ".pkl, version " + str(self.version) + ", " + size
		else:
			return "facebook_database version " + str(self.version) + ", " + size

	# called by pickle.dump
	# to avoid recursion limit errors,
	# changes instance pointers to id numbers for pickling
	def __getstate__(self):
		# we must build new state dictionary from scratch to avoid changing self
		# we need to switch instance pointers to id numbers
		# otherwise recursion limit errors are generated
		switch = {
			'friends',
			'rev_friends',
			'family',
			'rev_family',
			'possfam',
			'rev_possfam',
			'groups',
			'rev_groups',
			'members',
			'rev_members'}

		allusers = {} # new dictionary for fb users
		for u in self.users.values():
			newuser = facebook_user.__new__(facebook_user)
			for item in u.__dict__.keys():
				if item in switch:
					old  = u.__dict__[item]
					if type(old) == dated_dict:
						new = dated_dict.__new__(dated_dict)
						new.__dict__ = old.__dict__.copy()
						new[old.keydate()] = [v.id for v in old()]
					else:
						new = [v.id for v in old]
				else:
					new = u.__dict__[item]
				newuser.__dict__[item] = new
			allusers[u.id] = newuser

		allgroups = {} # new dictionary for fb groups
		for g in self.groups.values():
			newgroup = facebook_group.__new__(facebook_group)
			for item in g.__dict__.keys():
				if item in switch:
					old  = g.__dict__[item]
					if type(old) == dated_dict:
						new = dated_dict.__new__(dated_dict)
						new.__dict__ = old.__dict__.copy()
						new[old.keydate()] = [v.id for v in old()]
					else:
						new = [v.id for v in old]
				else:
					new = g.__dict__[item]
				newgroup.__dict__[item] = new
			allgroups[g.id] = newgroup

		data = {} # new dictionary for database
		data['users'] = allusers
		data['groups'] = allgroups
		data['file'] = self.file
		return data

	# called by pickle.load
	# changes id numbers back to instance pointers
	# also implements version control, reformatting old data via reformat_data.py
	def __setstate__(self, data):
		if 'version' not in data.keys():
			# need to reformat the previously saved data
			# this is a one-time operation
			self.__dict__ = data
			import error_check
			error_check.reformat(self, None)
			return

		# we need to switch id numbers back to instance pointers
		switch = {
			'friends',
			'family',
			'possfam',
			'groups',
			'members'}
		rev_switch = {'rev_' + item for item in switch}

		self.__dict__ = data

		for u in self.users.values():
			for item in u.__dict__.keys():
				if item in rev_switch:
					if item != 'rev_groups':
						u.__dict__[item] = [self.users[v] for v in u.__dict__[item]]
					else:
						u.__dict__[item] = [self.groups[v] for v in u.__dict__[item]]
				if item in switch:
					obj = u.__dict__[item] # instance of dated_dict
					if obj() != None:
						if item != 'groups':
							obj[obj.keydate()] = [self.users[v] for v in obj()]
						else:
							obj[obj.keydate()] = [self.groups[v] for v in obj()]

		for g in self.groups.values():
			for item in g.__dict__.keys():
				if item in rev_switch:
					g.__dict__[item] = [self.users[v] for v in g.__dict__[item]]
				if item in switch:
					obj = g.__dict__[item] # instance of dated_dict
					if obj() != None:
						obj[obj.keydate()] = [self.users[v] for v in obj()]

	# saves the database to the file self.file_name + ".pkl"
	# also saves a backup to the file self.file_name + "-backup.pkl"
	def save(self):
		if self.file == None:
			raise Exception("file path not set")
		pickle.dump(self, open(self.file + ".pkl", 'wb'))
		shutil.copy(self.file + ".pkl", self.file + "-backup.pkl")
		return

	# save database in 'data-archive' subfolder with a time-stamped file name
	def archive_save(self):
		now = datetime.datetime.now()
		now_string = str(now)
		now_string = now_string.replace(':', '-')
		now_string = now_string.replace('.', '-')

		if self.file == None:
			raise Exception("file name not set")
		if not os.path.isdir("data-archive"):
			os.makedirs("data-archive")
		pickle.dump(self, open("data-archive/" + self.file + " " + now_string + ".pkl", 'wb'))

	# add a user to the database
	def add_user(self, user_id, monitor, username = None, name = None):

		if type(user_id) != str or user_id.isdigit() == False:
			raise Exception("Incorrect argument given for user_id")
		if type(monitor) != bool:
			raise Exception("monitor must be of Boolean type")
		if username != None and type(username) != str:
			raise Exeption("username must be a string")
		if name != None and type(name) != str:
			raise Exception("name must be a string")

		if user_id in self.users and monitor:
			self.users[user_id].set_monitor(monitor)
		if user_id not in self.users:
			self.users[user_id] = facebook_user(user_id, monitor, username, name)

	# uses username to find and return facebook_user object from the database
	def get_user(self, username):
		hits = []
		for u in self.users.values():
			for v in u.username.values():
				if v == username:
					hits.append(u)

		if len(hits) == 0:
			return None
		if len(hits) == 1:
			return hits[0]
		return hits

	# returns list of facebook_user objects from the database
	# searches all name values for the search_text
	# search_text can be a string or a list of strings
	def search_user_names(self, search_text):
		if type(search_text) == str:
			search_text = [search_text]
		hits = []
		for u in self.users.values():
			adduser = False
			for v in u.name.values():
				for s in search_text:
					if v != None and v.find(s) != -1:
						adduser = True
			if adduser == True:
				hits.append(u)
		return hits

	# extracts items in update_items for every user_id in update_ids
	# updates and saves the database
	# when display == True, prints status updates during execution
	# if driver == None then it will return selenium.webdriver object
	def update_users(self, update_ids, update_items, driver = None, display = True):
		if driver == None:
			driver = extract_data.get_logged_in_driver()
			return_driver = True
		else:
			return_driver = False

		for userid in update_ids:
			if userid not in self.users:
				raise Exception(userid + " is not in the database yet")
			if self.users[userid].monitor == False:
				raise Exception(userid + " has attribute monitor == False")

		if display:
			print("")
			print("Fields being updated:")
			for item in update_items:
				print("-- " + item)

		for userid in update_ids:
			user = self.users[userid]
			
			if display:
				print("Extracting data for " + userid)
			try:
				newdata = extract_data.extract_items_for_user(driver, update_items, userid)
			except:
				if display:
					print("Failed to extract data.")
				newdata = {}


			if 'enabled' in newdata.keys():
				user.enabled.update(newdata['enabled'])
			if 'username' in newdata.keys():
				user.username.update(newdata['username'])
			if 'name' in newdata.keys():
				user.name.update(newdata['name'])
			if 'altname' in newdata.keys():
				user.altname.update(newdata['altname'])
			if 'intro' in newdata.keys():
				user.intro.update(newdata['intro'])
			if 'cities' in newdata.keys():
				user.cities.update(newdata['cities'])
			if 'work' in newdata.keys():
				user.work.update(newdata['work'])
			if 'edu' in newdata.keys():
				user.edu.update(newdata['edu'])
			if 'contact' in newdata.keys():
				user.contact.update(newdata['contact'])
			if 'basic' in newdata.keys():
				user.basic.update(newdata['basic'])
			if 'details' in newdata.keys():
				user.details.update(newdata['details'])
			if 'romantic' in newdata.keys():
				user.romantic.update(newdata['romantic'])
			if 'milestones' in newdata.keys():
				user.milestones.update(newdata['milestones'])
			if 'quotes' in newdata.keys():
				user.quotes.update(newdata['quotes'])
			if False and 'checkins' in newdata.keys():
				None
			if False and 'reviews' in newdata.keys():
				None
			if 'friends' in newdata.keys():
				frlist = []
				for fr in newdata['friends']:
					self.add_user(fr['id'], False, fr['username'], fr['name'])
					friend = self.users[fr['id']]
					frlist.append(friend)
					if user not in friend.rev_friends:
						friend.rev_friends.append(user)
				user.friends.update(frlist)
			if 'possfam' in newdata.keys():
				pflist = []
				for pf in newdata['possfam']:
					self.add_user(pf['id'], False, pf['username'], pf['name'])
					person = self.users[pf['id']]
					pflist.append(person)
					if user not in person.rev_possfam:
						person.rev_possfam.append(user)
				user.possfam.update(pflist)
			if 'family' in newdata.keys():
				falist = []
				for fa in newdata['family']:
					if 'id' in fa.keys():
						self.add_user(fa['id'], False, fa['username'], fa['name'])
						fam = self.users[fa['id']]
						falist.append(fam)
						if user not in fam.rev_family:
							fam.rev_family.append(user)
				user.family.update(falist)
				user.family_details.update(newdata['family'])
			if 'groups' in newdata.keys():
				glist = []
				for g in newdata['groups']:
					self.add_group(g['id'], False, g['url'], g['name'], g['size'])
					fbgroup = self.groups[g['id']]
					glist.append(fbgroup)
					if user not in fbgroup.rev_members:
						fbgroup.rev_members.append(user)
				user.groups.update(glist)
			if False and 'likes' in newdata.keys():
				None
			if False and 'events' in newdata.keys():
				None
			if False and 'followers' in newdata.keys():
				None
			if False and 'following' in newdata.keys():
				None


			time.sleep(LONG_WAIT)

		self.save()
		if display:
			print("Completed and saved")

		if return_driver:
			return driver
		else:
			return

	# add a group to the database
	def add_group(self, group_id, monitor, group_url = None, name = None, size = None):
		if type(group_id) != str or group_id.isdigit() == False:
			raise Exception("Incorrect argument given for group_id")
		if type(monitor) != bool:
			raise Exception("monitor must be of Boolean type")
		if group_url != None and type(group_url) != str:
			raise Exeption("group_url must be a string")
		if name != None and type(name) != str:
			raise Exception("name must be a string")
		if size != None and type(size) != int:
			raise Exception("size must be an integer")

		if group_id in self.groups and monitor:
			self.groups[group_id].set_monitor(monitor)
		if group_id not in self.groups:
			self.groups[group_id] = facebook_group(group_id, monitor, group_url, name, size)

	# uses group_url to find and return facebook_group object from the database
	def get_group(self, group_url):
		hits = []
		for g in self.groups.values():
			for v in g.url.values():
				if v == group_url:
					hits.append(g)
		if len(hits) == 0:
			return None
		if len(hits) == 1:
			return hits[0]
		return hits

	# returns list of facebook_group objects from the database
	# searches all group name values for the search_text
	# search_text can be a string or a list of strings
	def search_group_names(self, search_text):
		if type(search_text) == str:
			search_text = [search_text]
		hits = []
		for g in self.groups.values():
			addgroup = False
			for v in g.name.values():
				for s in search_text:
					if v != None and v.find(s) != -1:
						addgroup = True
			if addgroup == True:
				hits.append(g)
		return hits

	# extracts items in update_items for every group_id in group_ids
	# updates and saves the database
	# when display == True, prints status updates during execution
	# if driver == None then it will return selenium.webdriver object
	def update_groups(self, group_ids, update_items, driver = None, display = True):
		if driver == None:
			driver = extract_data.get_logged_in_driver()
			return_driver = True
		else:
			return_driver = False

		for groupid in group_ids:
			if groupid not in self.groups:
				raise Exception(groupid + " is not in the database yet")
			if self.groups[groupid].monitor == False:
				raise Exception(groupid + " has attribute monitor == False")

		if display:
			print("")
			print("Fields being updated:")
			for item in update_items:
				print("-- " + item)

		for groupid in group_ids:
			group = self.groups[groupid]

			if display:
				print("Extracting data for " + groupid)
			try:
				newdata = extract_data.extract_items_for_group(driver, update_items, groupid)
			except:
				if display:
					print("Failed to extract data.")
				newdata = {}

			if 'members' in newdata.keys():
				mlist = []
				for p in newdata['members']:
					group.member_details[p['id']] = p['details']
					self.add_user(p['id'], False, p['username'], p['name'])
					person = self.users[p['id']]
					mlist.append(person)
					if group not in person.rev_groups:
						person.rev_groups.append(group)
				group.members.update(mlist)

			time.sleep(LONG_WAIT)

		self.save()
		if display:
			print("Completed and saved")

		if return_driver:
			return driver
		else:
			return

	# returns a random user as instance of facebook_user
	def random_user(self, monitor=True):
		if monitor:
			potential = []
			for u in self.users.values():
				if u.monitor:
					potential.append(u)
		else:
			potential = list(self.users.values())

		i = randint(0, len(potential))
		return potential[i]

	# returns a random group as instance of facebook_group
	def random_group(self, monitor=True):
		if monitor:
			potential = []
			for g in self.groups.values():
				if g.monitor:
					potential.append(g)
		else:
			potential = list(self.groups.values())

		i = randint(0, len(potential))
		return potential[i]
