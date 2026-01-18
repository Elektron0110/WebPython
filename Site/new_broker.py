from flask import send_file, render_template, request
from flask import Blueprint as Flask
import matplotlib.pyplot as plt
import io, os, json, math
from datetime import datetime as dt
from datetime import timedelta as td
import plotly.express as px
import pandas as pd
from requests import get

app = Flask(__name__, 'new_broker')

@app.route('/Ums/text')
def sr():
	if os.path.isfile('data'):
		import json
		text = ''
		data: dict[str, dict[str, str]] = json.loads(open('data', 'r').read())
		for um in data:
			text += um+': '
			for k in data[um]:
				text += f'{k}: {data[um][k]}, '
			text = text[:-2]+'.\n'
		return '<meta http-equiv="refresh" content="60">'+text.replace('\n', '<br>')
	else: return 'Запустите "Брокер" для работы данной вкладки.'

@app.route('/Ums/secret')
def show_graph():
	if os.path.isfile(f'graph/{dt.today().strftime('%Y.%m.%d')}'):
		datae: dict[str, dict[str, str]] = json.loads(open(f'graph/{dt.today().strftime('%Y.%m.%d')}', 'r').read())
		# Create a plot
		plt.figure()
		plt.plot([dt.strptime(t, '%Y.%m.%d %H:%M:%S') for t in datae], # type: ignore
		   [[float(datae[t][k]) for k in datae[t]] for t in datae]) # type: ignore
		plt.title("График УМа")
		plt.xlabel("Время")
		plt.ylabel("Значение")
		
		# Save it to a temporary buffer.
		buf = io.BytesIO()
		plt.savefig(buf, format='png')
		buf.seek(0)

		# Send buffer in a response
		return send_file(buf, mimetype='image/png')
	return 'Запустите "Брокер" для работы данной вкладки.'

@app.route('/Ums')
def index():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') >= dt(2025, 8, 18) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	if date in os.listdir('graph'):
		datae: dict[str, dict[str, str]] = json.loads(open(f'graph/{date}', 'r').read())
		weather: dict[str, list[str | dt | float]] = dict(topic=[], time=[], value=[])
		for time in datae:
			for data in datae[time]:
				if 'P' not in data:
					weather['topic'].append(data)
					weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M:%S'))
					weather['value'].append(float(datae[time][data]))
		df = pd.DataFrame(weather)
		df['value'] = df.groupby('topic')['value'].transform(
			lambda x: x.rolling(window=10, min_periods=1).mean())
		fig = px.line(df, 'time', 'value', color="topic", markers=True)
		graph_html = fig.to_html(full_html=False)

		return render_template(f'graph.html', graph=graph_html,
						 dt_0=dt_0,
						 dt_1=dt_1)
	else: return f'''
Неправильный формат даты.
<br>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_0) if dt_0 else ""}" title="{dt_0 if dt_0 else "Дальше данных нет!"}">-1 день</a>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_1) if dt_1 else ""}" title="{dt_1 if dt_1 else "Дальше данных нет!"}">+1 день</a>
'''

@app.route('/Ums/hard')
def hindex():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') >= dt(2025, 8, 18) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	if date in os.listdir('graph'):
		datae: dict[str, dict[str, str]] = json.loads(open(f'graph/{date}', 'r').read())
		weather: dict[str, list[str | dt | float]] = dict(topic=[], time=[], value=[])
		for time in datae:
			for data in datae[time]:
				if 'P' not in data:
					weather['topic'].append(data)
					weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M:%S'))
					weather['value'].append(float(datae[time][data]))
		df = pd.DataFrame(weather)
		fig = px.line(df, 'time', 'value', color="topic", markers=True)
		graph_html = fig.to_html(full_html=False)

		return render_template(f'graph.html', graph=graph_html,
						 dt_0=dt_0,
						 dt_1=dt_1)
	else: return f'''
Неправильный формат даты.
<br>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_0) if dt_0 else ""}" title="{dt_0 if dt_0 else "Дальше данных нет!"}">-1 день</a>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_1) if dt_1 else ""}" title="{dt_1 if dt_1 else "Дальше данных нет!"}">+1 день</a>
'''

@app.route('/Ums/pressure')
def press():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') > dt(2026, 1, 1) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	if date in os.listdir('graph'):
		datae: dict[str, dict[str, str]] = json.loads(open(f'graph/{date}', 'r').read())
		weather: dict[str, list[str | dt | float]] = dict(topic=[], time=[], value=[])
		for time in datae:
			for data in datae[time]:
				if 'P' in data:
					weather['topic'].append(data)
					weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M:%S'))
					weather['value'].append(float(datae[time][data])/(400/3))
		df = pd.DataFrame(weather)
		df['value'] = df.groupby('topic')['value'].transform(
			lambda x: x.rolling(window=10, min_periods=1).mean())
		fig = px.line(df, 'time', 'value', color="topic", markers=True)
		graph_html = fig.to_html(full_html=False)

		return render_template(f'graph.html', graph=graph_html,
						 dt_0=dt_0,
						 dt_1=dt_1)
	else: return f'''
Неправильный формат даты.
<br>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_0) if dt_0 else ""}" title="{dt_0 if dt_0 else "Дальше данных нет!"}">-1 день</a>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_1) if dt_1 else ""}" title="{dt_1 if dt_1 else "Дальше данных нет!"}">+1 день</a>
'''

@app.route('/Ums/pressure/hard')
def hpress():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') > dt(2026, 1, 1) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	if date in os.listdir('graph'):
		datae: dict[str, dict[str, str]] = json.loads(open(f'graph/{date}', 'r').read())
		weather: dict[str, list[str | dt | float]] = dict(topic=[], time=[], value=[])
		for time in datae:
			for data in datae[time]:
				if 'P' in data:
					weather['topic'].append(data)
					weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M:%S'))
					weather['value'].append(float(datae[time][data])/(400/3))
		df = pd.DataFrame(weather)
		fig = px.line(df, 'time', 'value', color="topic", markers=True)
		graph_html = fig.to_html(full_html=False)

		return render_template(f'graph.html', graph=graph_html,
						 dt_0=dt_0,
						 dt_1=dt_1)
	else: return f'''
Неправильный формат даты.
<br>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_0) if dt_0 else ""}" title="{dt_0 if dt_0 else "Дальше данных нет!"}">-1 день</a>
<a style="color: chocolate; text-decoration: none;" href="{("/Ums?date="+dt_1) if dt_1 else ""}" title="{dt_1 if dt_1 else "Дальше данных нет!"}">+1 день</a>
'''

@app.route('/sun')
def sun():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') >= dt(2025, 8, 18) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	open(f'sun/{date}', 'w').write(get(f'https://xras.ru/txt/xray_S0KJ_{date.replace('.','')}.json').text)
	datae: list[dict[str, str]] = json.loads(open(f'sun/{date}', 'r').read())['data']
	weather: dict[str, list[dt | float]] = dict(time=[], value=[])
	for tv in datae:
		weather['time'].append(dt.strptime(tv['time'], '%Y-%m-%dT%H:%M:%S'))
		weather['value'].append(math.log(float(tv['long']), 10)*0.000001)
	df = pd.DataFrame(weather)
	fig = px.line(df, 'time', 'value', markers=True)
	fig.update_layout(
                  legend=dict(x=.5, xanchor="center"),
                  title='Вспышки на Солнце (GOES-18)',
                  xaxis_title="Время (UTC+3)",
                  yaxis_title="Вт/м²")
	fig.update_yaxes(range=[-9*0.000001, -2*0.000001],
				  	 tickvals=[-9*0.000001, -8*0.000001, -7*0.000001, -6*0.000001, -5*0.000001, -4*0.000001, -3*0.000001, -2*0.000001],
					 ticktext=['10⁻⁹', '10⁻⁸(A)', '10⁻⁷(B)', '10⁻⁶(C)', '10⁻⁵(M)', '10⁻⁴(X)', '10⁻³(X10)', '10⁻²'])
	fig.update_xaxes(range=[dt.strptime(date, '%Y.%m.%d')-td(1), dt.strptime(date+' 23:59', '%Y.%m.%d %H:%M')])
	graph_html = fig.to_html(full_html=False)

	return render_template(f'sun.html', graph=graph_html, dt_0=dt_0, dt_1=dt_1, loc=locate())

@app.route('/sun/average')
def sunaver():
	date = request.args.get('date')
	if not date: date = dt.today().strftime("%Y.%m.%d")
	dt_0 = (dt.strptime(date, '%Y.%m.%d')-td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') >= dt(2025, 8, 18) else None
	dt_1 = (dt.strptime(date, '%Y.%m.%d')+td(1)).strftime('%Y.%m.%d') if dt.strptime(date, '%Y.%m.%d') < dt.today()-td(1) else None
	# Пример данных
	open(f'sun/{date}', 'w').write(get(f'https://xras.ru/txt/xray_S0KJ_{date.replace('.','')}.json').text)
	datae: list[dict[str, str]] = json.loads(open(f'sun/{date}', 'r').read())['data']
	weather: dict[str, list[dt | float | str]] = dict(time=[], value=[], type=[])
	sun: list[int] = []
	for tv in datae:
		sun.append(math.log(float(tv['long']), 10)*0.000001)
		weather['time'].append(dt.strptime(tv['time'], '%Y-%m-%dT%H:%M:%S'))
		weather['value'].append(math.log(float(tv['long']), 10)*0.000001)
		weather['type'].append('SA')
		weather['time'].append(dt.strptime(tv['time'], '%Y-%m-%dT%H:%M:%S'))
		weather['value'].append(sum(sun)/len(sun))
		weather['type'].append('Среднее')
	df = pd.DataFrame(weather)
	fig = px.line(df, 'time', 'value', color='type', markers=True)
	fig.update_layout(
                  legend=dict(x=.5, xanchor="center"),
                  title='Вспышки на Солнце (GOES-18)',
                  xaxis_title="Время (UTC+3)",
                  yaxis_title="Вт/м²")
	fig.update_yaxes(range=[-9*0.000001, -2*0.000001],
				  	 tickvals=[-9*0.000001, -8*0.000001, -7*0.000001, -6*0.000001, -5*0.000001, -4*0.000001, -3*0.000001, -2*0.000001],
					 ticktext=['10⁻⁹', '10⁻⁸(A)', '10⁻⁷(B)', '10⁻⁶(C)', '10⁻⁵(M)', '10⁻⁴(X)', '10⁻³(X10)', '10⁻²'])
	fig.update_xaxes(range=[dt.strptime(date, '%Y.%m.%d')-td(1), dt.strptime(date+' 23:59', '%Y.%m.%d %H:%M')])
	graph_html = fig.to_html(full_html=False)
	return render_template(f'sun.html', graph=graph_html, dt_0=dt_0, dt_1=dt_1)

def locate():
	URL = 'https://api.sunrise-sunset.org/json'
	par = {
		'lat': 60,
		'lng': 30
	}
	res = get(URL, params=par, timeout=60)
	res: dict[str, str] = res.json()['results']

	ch = int(dt.now().strftime("%H"))
	cm = int(dt.now().strftime("%M"))

	uh = int(res['sunrise'][:res['sunrise'].find(':')])+3
	um = int(res['sunrise'][res['sunrise'].find(':')+1:res['sunrise'].rfind(':')])
	dh = int(res['sunset'][:res['sunset'].find(':')])+12+3
	dm = int(res['sunset'][res['sunset'].find(':')+1:res['sunset'].rfind(':')])

	a1 = ch - uh
	a2 = cm - um
	a3 = a1 * 60
	a4 = a2 + a3
	a5 = dh - uh
	a6 = dm - um
	a7 = a5 * 60 + a6
	a8 = a7 / 180
	a9 = a4 / a8

	q = a9
	q1 = (q * 5) / 9
	qw = str(int(q1)) + "%"
	ni = "мин."
	nii = "ч."
	if q > 180:
		q1 = ((ch * 60 + cm) - (dh * 60 + dm)) % 60
		q2 = int(((ch * 60 + cm) - (dh * 60 + dm)) / 60)
		if int(str(q1)[-1]) == 1:
			ni = "минуту"
		if int(str(q1)[-1]) > 4:
			ni = "минут"
		elif 1 < int(str(q1)[-1]) < 5:
			ni = "минуты"
		if int(str(q2)[-1]) == 1:
			nii = "час"
		if int(str(q2)[-1]) > 2:
			nii = "часа"
		elif int(str(q2)[-1]) in [0, 5, 6, 7, 8, 9]:
			nii = "часов"
		return f"Солнце зашло за горизонт {q2} {nii} {q1} {ni} назад."
	if q < 0:
		q1 = ((uh * 60 + um) - (ch * 60 + cm)) % 60
		q2 = int(((uh * 60 + um) - (ch * 60 + cm)) / 60)
		if int(str(q1)[-1]) == 1:
			ni = "минуту"
		if int(str(q1)[-1]) > 4:
			ni = "минут"
		elif 1 < int(str(q1)[-1]) < 5:
			ni = "минуты"
		if int(str(q2)[-1]) == 1:
			nii = "час"
		if int(str(q2)[-1]) > 2:
			nii = "часа"
		elif int(str(q2)[-1]) in [0, 5, 6, 7, 8, 9]:
			nii = "часов"
		return f"Солнце взайдёт из-за горизонта через {q2} {nii} {q1} {ni}."
	return f'Солнце прошло {qw} своего дневного пути по небосводу.'