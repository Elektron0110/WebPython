from flask import Blueprint, request
import json

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
	if req["session"]["new"]:
		response['response']['text'] = '(Приветствие)'
	else:
		response['response']['text'] = '(Ответ)'

	return json.dumps(response)
