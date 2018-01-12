import os
import datetime
import time
import pickle
import extract_data

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

		# lists of id numbers
		self.rev_friends = [] # people who list user as friend
		self.rev_family = [] # people who list user as family
		self.rev_possfam = [] # people who list user as friend and have same last name
		self.rev_groups = [] # groups that list user as member

		self.set_monitor(monitor)

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
		self.family = dated_dict(full_history = False)

		# list of id numbers
		self.possfam = dated_dict(full_history = False) # friends they list who have same last name
		self.friends = dated_dict(full_history = False) # friends they list
		self.followers = dated_dict(full_history = False) # Not functioning yet
		self.following = dated_dict(full_history = False) # Not functioning yet
		self.groups = dated_dict(full_history = False) # FB groups they are a member of
		self.events = dated_dict(full_history = False) # Not functioning yet
		self.likes = dated_dict(full_history = False) # Not functioning yet


		self.checkins = dated_dict(full_history = False) # Not functioning yet
		self.reviews = dated_dict(full_history = False) # Not functioning yet
		self.quotes = dated_dict(full_history = False) # quotes they list on their about page


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

		self.rev_members = []

		self.set_monitor(monitor)

	# set the value of the monitor attribute
	def set_monitor(self, monitor):
		if self.monitor == monitor:
			return
		self.monitor = monitor

		if self.monitor == False:
			return

		self.about = dated_dict()
		self.admins = dated_dict(full_history = False)
		self.members = dated_dict(full_history = False)
		self.member_details = {}




class facebook_database:

	# creates new instance of facebook_database class
	# file_name is the file name for saving the database
	def __init__(self, file_name = None):
		self.users = {} # dictionary where keys are user_id numbers and values are facebook_user objects
		self.groups = {} # dictionary where keys are group_id numbers and values are facebook_group objects
		self.file = file_name

	# saves the database to the file self.file_name + ".pkl"
	# also saves a backup to the file self.file_name + "-backup.pkl"
	def save(self):
		if self.file == None:
			raise Exception("file path not set")
		pickle.dump(self, open(self.file + ".pkl", 'wb'))
		pickle.dump(self, open(self.file + "-backup.pkl", 'wb'))
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
			
			if display:
				print("Extracting data for " + userid)
			try:
				newdata = extract_data.extract_items_for_user(driver, update_items, userid)
			except:
				if display:
					print("Failed to extract data.")
				newdata = {}


			if 'enabled' in newdata.keys():
				self.users[userid].enabled.update(newdata['enabled'])
			if 'username' in newdata.keys():
				self.users[userid].username.update(newdata['username'])
			if 'name' in newdata.keys():
				self.users[userid].name.update(newdata['name'])
			if 'altname' in newdata.keys():
				self.users[userid].altname.update(newdata['altname'])
			if 'intro' in newdata.keys():
				self.users[userid].intro.update(newdata['intro'])
			if 'cities' in newdata.keys():
				self.users[userid].cities.update(newdata['cities'])
			if 'work' in newdata.keys():
				self.users[userid].work.update(newdata['work'])
			if 'edu' in newdata.keys():
				self.users[userid].edu.update(newdata['edu'])
			if 'contact' in newdata.keys():
				self.users[userid].contact.update(newdata['contact'])
			if 'basic' in newdata.keys():
				self.users[userid].basic.update(newdata['basic'])
			if 'details' in newdata.keys():
				self.users[userid].details.update(newdata['details'])
			if 'romantic' in newdata.keys():
				self.users[userid].romantic.update(newdata['romantic'])
			if 'milestones' in newdata.keys():
				self.users[userid].milestones.update(newdata['milestones'])
			if 'quotes' in newdata.keys():
				self.users[userid].quotes.update(newdata['quotes'])
			if False and 'checkins' in newdata.keys():
				None
			if False and 'reviews' in newdata.keys():
				None
			if 'friends' in newdata.keys():
				frlist = []
				for fr in newdata['friends']:
					frlist.append(fr['id'])
					self.add_user(fr['id'], False, fr['username'], fr['name'])
					if userid not in self.users[fr['id']].rev_friends:
						self.users[fr['id']].rev_friends.append(userid)
				self.users[userid].friends.update(frlist)
			if 'possfam' in newdata.keys():
				pflist = []
				for pf in newdata['possfam']:
					pflist.append(pf['id'])
					self.add_user(pf['id'], False, pf['username'], pf['name'])
					if userid not in self.users[pf['id']].rev_possfam:
						self.users[pf['id']].rev_possfam.append(userid)
				self.users[userid].possfam.update(pflist)
			if 'family' in newdata.keys():
				for fa in newdata['family']:
					if 'id' in fa.keys():
						self.add_user(fa['id'], False, fa['username'], fa['name'])
						if userid not in self.users[fa['id']].rev_family:
							self.users[fa['id']].rev_family.append(userid)
				self.users[userid].family.update(newdata['family'])
			if 'groups' in newdata.keys():
				glist = []
				for g in newdata['groups']:
					glist.append(g['id'])
					self.add_group(g['id'], False, g['url'], g['name'], g['size'])
					if userid not in self.groups[g['id']].rev_members:
						self.groups[g['id']].rev_members.append(userid)
				self.users[userid].groups.update(glist)
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
				for user in newdata['members']:
					mlist.append(user['id'])
					self.groups[groupid].member_details[user['id']] = user['details']
					self.add_user(user['id'], False, user['username'], user['name'])
					if groupid not in self.users[user['id']].rev_groups:
						self.users[user['id']].rev_groups.append(groupid)
				self.groups[groupid].members.update(mlist)

			time.sleep(LONG_WAIT)

		self.save()
		if display:
			print("Completed and saved")

		if return_driver:
			return driver
		else:
			return
