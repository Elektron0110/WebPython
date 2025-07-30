"""Модуль, отвечающий за работу почты."""
import os
import random
from flask import Blueprint
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

name = 'Почта'

work = Blueprint('work', __name__, template_folder='templates')
@work.route('/mail', methods=['GET', 'POST'])
def login():
	from Site import session, MMess, MUsers, UserInfo, AuthUser, new_user
	if request.method == 'GET':
		if 'user' in session:
			return render_template('MLK.html', name=name, session=session)
		else:
			return render_template('Mlogin.html')
	if request.method == 'POST':
		thing = request.form['thing']
		email = request.form['email']
		password = request.form['password']
		if thing == 'register':
			fn = request.form['f_name']
			sn = request.form['s_name']
			tn = request.form['t_name']
			tel = request.form['tel']
			b_day = request.form['b_day']
			new_user(email=email, password=password, s=sn, f=fn, t=tn, tel=tel, b_day=b_day)
		ui = UserInfo.query.filter_by(email=email).first()
		u = AuthUser.query.filter_by(email=email).first()
		if u:
			if password == u.password:
				session['user'] = f'{ui.s} {ui.f} {ui.t}'
				session['telephone'] = ui.tel
				session['birthday'] = ui.b_day
				session['email'] = ui.email
				return render_template('MLK.html', name=name, session=session)
			else:
				print(password, u.password)
				return 'Password in invalid.'
		else:
			return render_template('Mregister.html',
			                       email=email,
			                       password=password,
			                       date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
