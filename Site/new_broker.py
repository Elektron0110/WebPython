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
		plt.plot([dt.strptime(t, '%Y.%m.%d %H:%M') for t in datae], # type: ignore
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
				weather['topic'].append(data)
				weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M'))
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
		weather['value'].append(math.log(float(tv['long']), 10))
	df = pd.DataFrame(weather)
	fig = px.line(df, 'time', 'value', markers=True)
	fig.update_layout(legend_orientation="h",
                  legend=dict(x=.5, xanchor="center"),
                  title='Солнечная активность',
                  xaxis_title="Время (UTC+3)",
                  yaxis_title="Вт/м²")
	fig.update_yaxes(tickvals=[-8, -7, -6, -5, -4], ticktext=['A', 'B', 'C', 'M', 'X'])
	graph_html = fig.to_html(full_html=False)

	return render_template(f'sun.html', graph=graph_html, dt_0=dt_0, dt_1=dt_1)