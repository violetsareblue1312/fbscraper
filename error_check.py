import datetime
import pickle


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


def has_errors(data):
	utype = {}
	utype['checkins'] = None
	utype['reviews'] = None
	utype['quotes'] = str
	utype['username'] = str
	utype['possfam'] = str
	utype['friends'] = str
	utype['followers'] = None
	utype['following'] = None
	utype['groups'] = str
	utype['events'] = None
	utype['likes'] = None
	utype['name'] = str
	utype['enabled'] = bool
	utype['altname'] = str
	utype['intro'] = str
	utype['cities'] = list
	utype['work'] = list
	utype['edu'] = list
	utype['romantic'] = list
	utype['contact'] = dict
	utype['basic'] = dict
	utype['details'] = list
	utype['milestones'] = list
	utype['family'] = dict

	user_errors = set()
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


	for u in data.users.values():
		if type(u.monitor) != bool:
			user_errors.add('monitor')

		if type(u.id) != str or u.id.isdigit() == False:
			user_errors.add('id')
		if data.users[u.id] != u:
			user_errors.add('id')

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

		for v in u.rev_friends:
			if type(v) != str:
				user_errors.add('rev_friends')
			if u.id not in data.users[v].friends():
				user_errors.add('friend crossref')
		for v in u.rev_family:
			if type(v) != str:
				user_errors.add('rev_family')
			crossref = False
			for w in data.users[v].family():
				if 'id' in w.keys() and w['id'] == u.id:
					crossref = True
			if crossref == False:
				user_errors.add('family crossref')
		for v in u.rev_possfam:
			if type(v) != str:
				user_errors.add('rev_possfam')
			if u.id not in data.users[v].possfam():
				user_errors.add('possfam crossref')
		for v in u.rev_groups:
			if type(v) != str:
				user_errors.add('rev_groups')
			if u.id not in data.groups[v].members():
				user_errors.add('group crossref')

		for item, data_type in utype.items():
			if item in dir(u):
				dated_d = eval("u." + item)
				if dated_dict_has_type_errors(dated_d, data_type):
					user_errors.add(item)

		if u.monitor:
			for item in utype.keys():
				if item not in dir(u):
					user_errors.add(item)
			for v in u.friends():
				if u.id not in data.users[v].rev_friends:
					user_errors.add('friends crossref')
			for v in u.family():
				if 'id' in v.keys():
					cfamily += 1
				if 'id' in v.keys() and u.id not in data.users[v['id']].rev_family:
					user_errors.add('family crossref')
			for v in u.possfam():
				if u.id not in data.users[v].rev_possfam:
					user_erros.add('possfam crossref')
			for v in u.groups():
				if u.id not in data.groups[v].rev_members:
					user_errors.add('group crossref')
			cfriends += len(u.friends())
			cposs += len(u.possfam())
			cgmember += len(u.groups())

		crfriends += len(u.rev_friends)
		crfamily += len(u.rev_family)
		crposs += len(u.rev_possfam)
		crgroupm += len(u.rev_groups)


	gtype = {}
	gtype['url'] = str
	gtype['name'] = str
	gtype['size'] = int
	gtype['about'] = str
	gtype['admins'] = str
	gtype['members'] = str

	group_errors = set()

	for g in data.groups.values():
		if type(g.monitor) != bool:
			group_errors.add('monitor')

		if type(g.id) != str or g.id.isdigit() == False:
			group_errors.add('id')
		if data.groups[g.id] != g:
			group_errors.add('id')

		if 'name' not in dir(g):
			group_errors.add('name')
		if 'url' not in dir(g):
			group_errors.add('url')
		if 'size' not in dir(g):
			group_errors.add('size')
		if 'rev_members' not in dir(g):
			group_errors.add('rev_members')

		for v in g.rev_members:
			if type(v) != str:
				group_errors.add('rev_members')
			if g.id not in data.users[v].groups():
				group_errors.add('member crossref')

		for item, data_type in gtype.items():
			if item in dir(u):
				dated_d = eval("g." + item)
				if dated_dict_has_type_errors(dated_d, data_type):
					group_erros.add(item)

		if g.monitor:
			for item in gtype.keys():
				if item not in dir(g):
					group_errors.add(item)
			for v in g.members():
				if g.id not in data.users[v].rev_groups:
					group_errors.add('member crossref')
			cgroupm += len(g.members())

		crgmember += len(g.rev_members)

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

		if data.file != None:
			now = datetime.datetime.now()
			now_string = str(now)
			now_string = now_string.replace(':', '-')
			now_string = now_string.replace('.', '-')

			print(errors)
			pickle.dump(errors, open("data-archive/" + me.file + " error report " + now_string + ".pkl", 'wb'))

		return True