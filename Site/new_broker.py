from flask import send_file, render_template
from flask import Blueprint as Flask
import matplotlib.pyplot as plt
import io, os, json
from datetime import datetime as dt
import plotly.express as px
import pandas as pd

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
	if os.path.isfile('Site/graph'):
		datae: dict[str, dict[str, str]] = json.loads(open('graph', 'r').read())
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
def indexes():
	# Пример данных
	datae: dict[str, dict[str, str]] = json.loads(open('graph', 'r').read())
	weather: dict[str, list[str | dt | float]] = dict(topic=[], time=[], value=[])
	for time in datae:
		for data in datae[time]:
			weather['topic'].append(data)
			weather['time'].append(dt.strptime(time, '%Y.%m.%d %H:%M'))
			weather['value'].append(float(datae[time][data]))
	df = pd.DataFrame(weather)
	fig = px.line(df, 'time', 'value', color="topic")
	graph_html = fig.to_html(full_html=False)

	return render_template('graph.html', graph=graph_html)
