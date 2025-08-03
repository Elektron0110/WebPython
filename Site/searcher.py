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
		   'heading': 'Курс', 'altitude': 'Высота', 'ground_speed': 'Скорость', 'aircraft_code': 'Тип',
		   'registration': 'Регистрационный номер', 'origin_airport_iata': 'Аэропорт отправления',
		   'destination_airport_iata': 'Аэропорт прибытия', 'get_distance_from(Пулково)': 'Расстояние до Пулково',
		   'get_distance_from(Братск)': 'Расстояние до Братска', 'get_distance_from(Толмачёво)': 'Расстояние до Толмачёво',
		   'get_distance_from(Домодедово)': 'Расстояние до Домодедово', 'get_distance_from(Храброво)': 'Расстояние до Храброво',
		   'get_distance_from(Платов)': 'Расстояние до Платова', 'get_distance_from(Елизово)': 'Расстояние до Елизово'}
def fly(рейс):
	компания = str()
	for знак in рейс:
		if not знак.isdigit():
			компания += знак
	Авиакомпания = fr_api.get_flights(компания)
	for ac in Авиакомпания:
		if рейс == ac.callsign:
			for предмет in интерес:
				самолёт[интерес[предмет]] = eval(f'ac.{предмет}')
			if самолёт['Аэропорт прибытия']:
				прибытия = fr_api.get_airport(самолёт['Аэропорт прибытия'])
				прибытия = f'{прибытия.name} - {прибытия.city}'
				самолёт['Аэропорт прибытия'] = прибытия
			if самолёт['Аэропорт отправления']:
				отправления = fr_api.get_airport(самолёт['Аэропорт отправления'])
				отправления = f'{отправления.name} - {отправления.city}'
				самолёт['Аэропорт отправления'] = отправления
	return str(самолёт).replace("{", "").replace("}", "").replace(", ", "<br>").replace(": ", " ― ").replace("'", "")