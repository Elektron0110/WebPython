from flask import Blueprint, request
import json
from searcher import fly
from datetime import datetime

bp = Blueprint('alice', __name__)

@bp.route('/alice', methods=['POST'])
def alice():
	print(request.json)

	response = {
		'version': request.json["version"],
		'session': request.json["session"],
		'response': {
			"end_session": False
		}
	}

	req = request.json
	if req["session"]["new"] and not req['request']['command']:
		response['response']['text'] = 'Здраствуйте, меня зовут Авиатор Богданов, ну или же можете звать меня Александром Богдановым. ' \
                                       'Я - навык Яндекс Алисы. Я могу помочь Вам получить некоторую информацию ' \
                                       'о разных авиарейсах. Просто назовите мне номер интересующего Вас авиарейса. ' \
                                       'Например: SU-6336.' #(Приветствие)
	elif not req['request']['command'].replace(' ', '').isdigit():
		txt = str(req['request']['command']).replace('про рейс ', '')
		txt = txt.replace(' - ', ' ')
		txt = txt.replace('-', ' ')
		txt = txt.replace('про рис ', '')
		txt = txt.replace('прорис ', '')
		txt = txt.replace(' seven', '7')
		txt = txt.replace('су', 'SU')
		txt = txt.replace('s7', 'S7')
		txt = txt.replace('s 7', 'S7')
		txt = txt.replace('с 7', 'S7')
		txt = txt.replace('дп', 'DP')
		txt = txt.replace('ут', 'UT')
		txt = txt.replace('рв', 'RW')
		txt = txt.replace('зэд', 'Z')
		txt = txt.replace('эйч', 'H')
		txt = txt.replace('з', 'Z')
		txt = txt.replace('аш', 'H')
		txt = txt.replace('z h', 'ZH')
		txt = txt.replace('у ', 'U')
		txt = txt.replace('эн 4', 'N4')
		txt = txt.replace('5 эн', '5N')
		print(txt)
		text = txt.split(' ')
		if len(text) == 2:
			response['response']['text'] = fly(text).replace('<br>', '\n') #str(text) #'(Ответ)' #
			if fly(text):
				response['response']['end_session'] = True
			else:
				open('errors', 'a').write(txt+' '+datetime.now().strftime("%H:%M")+' '+req['meta']['client_id']+'\n')
				response['response']['text'] = 'Извините, что-то пошло не так. Возможно данный рейс уже приземлился, а возможно он находится вне нашей ' \
                                               'видимости, такое бывает. Но не волнуйтесь, как бы то ни было мы уже сообщили об этой ошибке нашим специалистам' \
                                               ', и вскоре проблема, если она есть, будет исправлена.\nА пока попробуйте получить информацию про другой рейс.'
			json.dump({'response': response, 'request': req}, open('alice.json', 'w'))
		else: response['response']['text'] = 'Прошу прощения, но я не могу найти информацию про рейс, номер которого состоит только из букв. В его конце ' \
                                             'должны быть четыре какие-либо цифры.\nВозможно Ваше устройство не расслышало Вас. Попробуйте ещё раз.'
	else: response['response']['text'] = 'Прошу прощения, но я не могу найти информацию про рейс, номер которого состоит только из цифр. В его начале ' \
                                         'должны быть какие-то две или три буквы.\nВозможно Ваше устройство не расслышало Вас. Попробуйте ещё раз.'
	return json.dumps(response)
