from json import dumps
from typing import Any
from FlightRadar24 import FlightRadar24API

fr_api = FlightRadar24API()
flight_tracker = fr_api.get_flight_tracker_config()
flight_tracker.vehicles = "0"
fr_api.set_flight_tracker_config(flight_tracker)
Пулково = fr_api.get_airport('LED')
Братск = fr_api.get_airport('BTK')
Толмачёво = fr_api.get_airport('OVB')
Домодедово = fr_api.get_airport('DME')
Храброво = fr_api.get_airport('KGD')
Платов = fr_api.get_airport('ROV')
Елизово = fr_api.get_airport('PKC')
самолёт: dict[str, Any] = {}
интерес = {'number': 'Рейс', 'airline_iata': 'Авиакомпания', 'latitude': 'Широта', 'longitude': 'Долгота',
		   'heading': 'Курс', 'altitude': 'Высота (в м)', 'ground_speed': 'Скорость (в км/ч.)', 'aircraft_code': 'Тип',
		   'registration': 'Регистрационный номер', 'origin_airport_iata': 'Аэропорт отправления',
		   'destination_airport_iata': 'Аэропорт прибытия', 'get_distance_from(Пулково)': 'Расстояние до Пулково (в км)',
		   'get_distance_from(Братск)': 'Расстояние до Братска (в км)', 'get_distance_from(Толмачёво)': 'Расстояние до Толмачёво (в км)',
		   'get_distance_from(Домодедово)': 'Расстояние до Домодедово (в км)', 'get_distance_from(Храброво)': 'Расстояние до Храброво (в км)',
		   'get_distance_from(Платов)': 'Расстояние до Платова (в км)', 'get_distance_from(Елизово)': 'Расстояние до Елизово (в км)'}
def fly(рейс: str | list[str]):
	if isinstance(рейс, str):
		рейс = рейс.split(' ')
	компания = рейс[0]
	компания = компания.replace('SU', 'AFL' if not 6000 < int(рейс[1]) < 7000 else 'SDM')
	компания = компания.replace('S7', 'SBI')
	компания = компания.replace('DP', 'PBD')
	компания = компания.replace('U6', 'SVR')
	компания = компания.replace('UT', 'UTA')
	компания = компания.replace('N4', 'NWS')
	компания = компания.replace('RW', 'RWD')
	компания = компания.replace('5N', 'AUL')
	рейс = компания+рейс[1]
	Авиакомпания = fr_api.get_flights(компания)
	print(рейс)
	for ac in Авиакомпания:
		if рейс == ac.callsign:
			for предмет in интерес:
				global самолёт
				самолёт[интерес[предмет]] = eval(f'ac.{предмет}')
				if str(eval(f'ac.{предмет}'))[0].isdigit():
					самолёт[интерес[предмет]] = round(eval(f'ac.{предмет}'), 2)
			if самолёт['Аэропорт прибытия']:
				прибытия = fr_api.get_airport(самолёт['Аэропорт прибытия'])
				прибытия = f'{прибытия.name} - {прибытия.city}'
				самолёт['Аэропорт прибытия'] = прибытия
			if самолёт['Аэропорт отправления']:
				отправления = fr_api.get_airport(самолёт['Аэропорт отправления'])
				отправления = f'{отправления.name} - {отправления.city}'
				самолёт['Аэропорт отправления'] = отправления
	if not самолёт:
		самолёт = ['Данный рейс находится вне нашего видения.',
				   'Другие рейсы этой авиакомпании:'] + [ac.callsign for ac in Авиакомпания]
	return str(самолёт).replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace(", ", "<br>").replace(": ", " ― ").replace("'", "")