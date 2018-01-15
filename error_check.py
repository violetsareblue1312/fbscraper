import datetime
import manage_data

# checks the data types of values stored in a dated dictionary
# when ._hist == False, its known the value will be a list,
# so in this case it checks the data types of the values stored in the list
# returns boolean
def dated_dict_has_type_errors(dated_d, data_type):
	error = False

	if type(dated_d._date) != datetime.date:
		error = True

	if dated_d._hist == False:
		if len(dated_d) > 1:
			error = True
		if type(list(dated_d.keys())[0]) != datetime.date:
			error = True
		if dated_d() != None and type(dated_d()) != list:
			error = True
		if type(dated_d()) == list:
			for v in dated_d():
				if type(v) != data_type:
					error = True
	else:
		for k, v in dated_d.items():
			if type(k) != datetime.date:
				error = True
			if v!= None and type(v) != data_type:
				error = True

	return error

# checks instance of facebook_database for errors
# may take a few minutes to execute
def has_errors(fb):
	# for user attributes of type dated_dict,
	# record the intended data type of stored values, except
	# when dated_dict has ._hist == False, we know the stored value will be a list,
	# so here we record the intended data types of the objects in the list
	utype = {
		'altname' : str,
		'basic' : dict,
		'checkins' : None,
		'cities' : list,
		'contact' : dict,
		'details' : list,
		'edu' : list,
		'enabled' : bool,
		'events' : None,
		'family': manage_data.facebook_user,
		'family_details' : dict,
		'followers' : None,
		'following' : None,
		'friends' : manage_data.facebook_user,
		'groups' : manage_data.facebook_group,
		'intro' : str,
		'likes' : None,
		'milestones' : list,
		'name' : str,
		'possfam' : manage_data.facebook_user,
		'quotes' : str,
		'reviews' : None,
		'romantic' : list,
		'username' : str,
		'work' : list
		}

	# these will count cross-references from both ends
	cfriends = 0
	crfriends = 0
	cfamily = 0
	crfamily = 0
	cposs = 0
	crposs = 0
	cgmember = 0
	crgmember = 0
	cgroupm = 0
	crgroupm = 0

	# this will store brief descriptive data of errors encountered
	user_errors = set()

	# cycle over all users and check each for errors
	for u in fb.users.values():
		if type(u.monitor) != bool:
			user_errors.add('monitor')

		if type(u.id) != str or u.id.isdigit() == False:
			user_errors.add('id')
		if fb.users[u.id] != u:
			user_errors.add('id')

		# check that the common attributes exist
		if 'name' not in dir(u):
			user_errors.add('name')
		if 'username' not in dir(u):
			user_errors.add('username')
		if 'rev_friends' not in dir(u):
			user_errors.add('rev_friends')
		if 'rev_family' not in dir(u):
			user_errors.add('rev_family')
		if 'rev_possfam' not in dir(u):
			user_errors.add('rev_possfam')
		if 'rev_groups' not in dir(u):
			user_errors.add('rev_groups')

		# check data-types and cross references for rev_* attributes
		for v in u.rev_friends:
			if type(v) != manage_data.facebook_user:
				user_errors.add('rev_friends')
			if u not in v.friends():
				user_errors.add('friend crossref')
		for v in u.rev_family:
			if type(v) != manage_data.facebook_user:
				user_errors.add('rev_family')
			if u not in v.family():
				user_errors.add('family crossref')
		for v in u.rev_possfam:
			if type(v) != manage_data.facebook_user:
				user_errors.add('rev_possfam')
			if u not in v.possfam():
				user_errors.add('family crossref')
		for g in u.rev_groups:
			if type(g) != manage_data.facebook_group:
				user_errors.add('rev_groups')
			if u not in g.members():
				user_errors.add('group crossref')

		# check data types for all attributes of type dated_dict
		for item, data_type in utype.items():
			if item in dir(u):
				dated_d = u.__dict__[item]
				if dated_dict_has_type_errors(dated_d, data_type):
					user_errors.add(item)

		# if monitored, check that all attributes exist
		# also check cross-references for friends, family, possfam, and groups
		if u.monitor:
			for item in utype.keys():
				if item not in dir(u):
					user_errors.add(item)
			for v in u.friends():
				if u not in v.rev_friends:
					user_errors.add('friends crossref')
			for v in u.family():
				if u not in v.rev_family:
					user_errors.add('family crossref')
			for v in u.possfam():
				if u not in v.rev_possfam:
					user_errors.add('possfam crossref')
			for g in u.groups():
				if u not in g.rev_members:
					user_errors.add('group crossref')
			# update cross-ref counts
			cfriends += len(u.friends())
			cfamily += len(u.family())
			cposs += len(u.possfam())
			cgmember += len(u.groups())

		# update reverse cross-ref counts
		crfriends += len(u.rev_friends)
		crfamily += len(u.rev_family)
		crposs += len(u.rev_possfam)
		crgroupm += len(u.rev_groups)

	# record the intended data type of stored values, similar to utype above
	gtype = {
		'url' : str,
		'name' : str,
		'size' : int,
		'about' : str,
		'admins' : manage_data.facebook_user,
		'members' : manage_data.facebook_user
		}

	# this will store brief descriptive data of errors encountered
	group_errors = set()

	for g in fb.groups.values():
		if type(g.monitor) != bool:
			group_errors.add('monitor')

		if type(g.id) != str or g.id.isdigit() == False:
			group_errors.add('id')
		if fb.groups[g.id] != g:
			group_errors.add('id')

		# check that the common attributes exist
		if 'name' not in dir(g):
			group_errors.add('name')
		if 'url' not in dir(g):
			group_errors.add('url')
		if 'size' not in dir(g):
			group_errors.add('size')
		if 'rev_members' not in dir(g):
			group_errors.add('rev_members')

		# check data types and cross-references for rev_members
		for u in g.rev_members:
			if type(u) != manage_data.facebook_user:
				group_errors.add('rev_members')
			if g not in u.groups():
				group_erros.add('member crossref')

		# check data types for all attributes of type dated_dict
		for item, data_type in gtype.items():
			if item in dir(u):
				dated_d = g.__dict__[item]
				if dated_dict_has_type_errors(dated_d, data_type):
					group_erros.add(item)

		# if monitored, check that all attributes are present
		# also check member cross-references
		if g.monitor:
			for item in gtype.keys():
				if item not in dir(g):
					group_errors.add(item)
			for u in g.members():
				if g not in u.rev_groups:
					group_erros.add('member crossref')
			# update cross-ref count
			cgroupm += len(g.members())

		# update reverse cross-ref count
		crgmember += len(g.rev_members)

	# compare cross-reference counts
	if cfriends != crfriends:
		user_errors.add('friend counts')
	if cfamily != crfamily:
		user_errors.add('family counts')
	if cposs != crposs:
		user_errors.add('possfam counts')
	if cgmember != crgmember:
		user_errors.add('group member count')
	if cgroupm != crgroupm:
		group_errors.add('group member count')

	if user_errors == set() and group_errors == set():
		return False
	else:
		errors = {}
		errors['users'] = user_errors
		errors['groups'] = group_errors
		print(errors)
		return True

# when no cities could be extracted, data was previously saved as list ['No places to show']
# this changes past saved data, changing ['No places to show'] to []
def correct_cities_info(fb):
	for u in fb.users.values():
		if u.monitor:
			for k, v in u.cities.items():
				if v == ['No places to show']:
					u.cities[k] = []

# changes lists that previously contained id numbers to now contain pointers to class instances
# also separates the user.family attribute
# family now lists family members on fb (as user instances)
# new attribute family_details lists all family (on and off fb) and lists details such as relation when available
def change_ids_to_pointers(fb):
	for u in fb.users.values():
		u.rev_friends = [fb.users[pid] for pid in u.rev_friends]
		u.rev_family = [fb.users[pid] for pid in u.rev_family]
		u.rev_possfam = [fb.users[pid] for pid in u.rev_possfam]
		u.rev_groups = [fb.groups[gid] for gid in u.rev_groups]

		if u.monitor:
			u.family_details = manage_data.dated_dict(full_history=False)
			u.family_details.pop(u.family_details.keydate())
			u.family_details._date = u.family._date
			u.family_details[u.family.keydate()] = u.family()

			if u.friends() != None:
				u.friends[u.friends.keydate()] = [fb.users[pid] for pid in u.friends()]
			if u.possfam() != None:
				u.possfam[u.possfam.keydate()] = [fb.users[pid] for pid in u.possfam()]
			if u.family() != None:
				u.family[u.family.keydate()] = [fb.users[person['id']] for person in u.family() if 'id' in person]
			if u.groups() != None:
				u.groups[u.groups.keydate()] = [fb.groups[gid] for gid in u.groups()]

	for g in fb.groups.values():
		g.rev_members = [fb.users[pid] for pid in g.rev_members]

		if g.monitor:
			if g.members() != None:
				g.members[g.members.keydate()] = [fb.users[pid] for pid in g.members()]

# reformats data that has no assigned version (the oldest data)
def no_version(fb):
	correct_cities_info(fb)
	change_ids_to_pointers(fb)
	fb.version = 1

# this method is auto called by facebook_database.__setstate__ during unpickling of data
# reformats old versions of data to make them up-to-date
def reformat(fb, version):
	if version == None:
		no_version(fb)
