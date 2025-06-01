from flask import render_template
from flask_sqlalchemy import SQLAlchemy


class Admin:
	def __init__(self, app, users, data, applications):
		self.app = app
		self.users = users
		self.data = data
		self.applications = applications
	def see(self):
		return render_template('AdmSee.html',
		                       u=self.users.query.all,
		                       d=self.data.query.all,
		                       a=self.applications.query.all)