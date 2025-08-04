from flask import Blueprint, request
import json
from searcher import fly

bp = Blueprint('alice', __name__)

@bp.route('/api/alice', methods=['POST'])
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
		response['response']['text'] = '(Приветствие)'
	else:
		txt = str(req['request']['command']).replace('про рейс ', '')
		txt = txt.replace('про рис ', '')
		txt = txt.replace('прорис ', '')
		txt = txt.replace(' seven', '7')
		txt = txt.replace('су', 'SU')
		txt = txt.replace('s7', 'S7')
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
		response['response']['text'] = fly(text).replace('<br>', '\n') #str(text) #'(Ответ)' #
		

	return json.dumps(response)
