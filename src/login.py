#
#   login.py
#
#   Copyright (C) 2006-2007 by Tyler Gates <TGates81@gmail.com>
#   Copyright (C) 2008 by Loui Chang <louipc.ist@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2
#   as published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import http.cookiejar
import os
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import http.client

class LoginError(Exception):
	# base exception
	pass

class CookieError(LoginError):
	# general cookie errors
	pass

class AuthenticationError(LoginError):
	# general login errors
	pass

class ActionError(LoginError):
	# general action errors
	pass

class TargetError(LoginError):
	# general target errors
	pass

class aurlogin:
	def __init__(self):
		self.cookie_jar = http.cookiejar.LWPCookieJar()
		self.aursite	= 'http://aur.archlinux.org/'
		self.headers    = {'User-agent':
			'Mozilla/4.0 (compatible; aurbuild/' + VERSION +')',
			'Content-type': 'application/x-www-form-urlencoded',
			'Accept': 'text/plain'}


	def get_cookie(self, cookiefile):
		""" get a cookie from the main site and save it to cookiefile """

		# create dirname of cookie file if not found
		cookie_dir = os.path.dirname(cookiefile)
		if not os.path.isdir(cookie_dir):
			try:
				os.makedirs(cookie_dir)
			except Exception as e:
				raise CookieError('could not create cookie directory `'+cookie_dir+'\'. '+str(e))

		req = urllib.request.Request(self.aursite, None, self.headers)
		handle = urllib.request.urlopen(req)
		# save the cookie
		self.cookie_jar.save(cookiefile)

	def logout(self):
		""" logout of the main site """

		try:
			req = urllib.request.Request(self.logout_url, None, self.headers)
			handle = urllib.request.urlopen(req)
		except:
			# fuck it
			pass

	def login(self, username, password, cookiefile):
		""" login to the main site """

		login_url = self.aursite
		login_params = urllib.parse.urlencode(
			{'user': username, 'pass': password})

		conn = http.client.HTTPConnection(aur_domain)
		conn.request("POST", "", login_params, self.headers)
		response = conn.getresponse()

		data = response.read()
		conn.close()


		# get a cookie
		if not os.path.isfile(cookiefile): self.get_cookie(cookiefile)

		# build an opener for the cookie
		self.cookie_jar.load(cookiefile)
		self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
		urllib.request.install_opener(self.opener)

		# login request
		req = urllib.request.Request(login_url, None, self.headers)
		handle = urllib.request.urlopen(req)

		# checked that we are logged in
		logged_in = 0
		for line in handle:
			if 'Logged-in as:' in line:
				logged_in = 1
				break
		if not logged_in:
			raise AuthenticationError('invalid username or password')

	def vote(self, username, password, cookiefile, pkgname):
		""" vote for pkgname and return 2 if already voted """

		search_url = self.aursite+'packages.php?K='+pkgname

		# login
		self.login(username, password, cookiefile)

		# query for pkgname
		req = urllib.request.Request(search_url, None, self.headers)
		handle = urllib.request.urlopen(req)
		lines = handle.readlines()
		valid_pkg = 0
		for line in lines:
			if '>'+pkgname+' ' in line:
				valid_pkg = 1
				# get the ID
				id = line.split('ID=')[1]
				id = id.split('&')[0]
				# the next 2 lines are voted status, get that
				cur = int(lines.index(line))
				voted = lines[cur+2]
				if not 'Yes' in voted:
					# haven't voted yet, do it
					vote_url = self.aursite+'packages.php?IDs['+id+']&do_Vote'
					req = urllib.request.Request(vote_url, None, self.headers)
					handle = urllib.request.urlopen(req)

					# confirm
					confirmed = 0
					for l in handle:
						if 'votes have been cast' in l:
							confirmed = 1
							self.logout()
							break
					if not confirmed:
						self.logout()
						raise ActionError('action confirmation indicates failure')
				else:
					# return 2 because the action has already been performed
					self.logout()
					return 2
				self.logout()
				return
		if not valid_pkg:
			self.logout()
			raise TargetError('`'+pkgname+'\' not found on host')


	def unvote(self, username, password, cookiefile, pkgname):
		""" un-vote for pkgname and return 2 if not voted """

		search_url = self.aursite+'packages.php?K='+pkgname

		# login
		self.login(username, password, cookiefile)

		# query for pkgname
		req = urllib.request.Request(search_url, None, self.headers)
		handle = urllib.request.urlopen(req)
		lines = handle.readlines()
		valid_pkg = 0
		for line in lines:
			if '>'+pkgname+' ' in line and 'packages.php?' in line:
				valid_pkg = 1
				# get the ID
				id = line.split('ID=')[1]
				id = id.split('&')[0]
				# the next 2 lines are voted status, get that
				cur = int(lines.index(line))
				voted = lines[cur+2]
				if 'Yes' in voted:
					# have voted, unvote
					voted_url = self.aursite+'packages.php?IDs['+id+']&do_UnVote'
					req = urllib.request.Request(voted_url, None, self.headers)
					handle = urllib.request.urlopen(req)

					# confirm
					confirmed = 0
					for l in handle:
						if 'have been removed' in l:
							confirmed = 1
							self.logout()
							break
					if not confirmed:
						self.logout()
						raise ActionError('action confirmation indicates failure')
				else:
					# return 2 because the action has already been performed
					self.logout()
					return 2
				self.logout()
				return
		if not valid_pkg:
			self.logout()
			raise TargetError('`'+pkgname+'\' not found on host')

