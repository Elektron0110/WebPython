from json import dumps
from typing import Any
from FlightRadar24 import FlightRadar24API

fr_api = FlightRadar24API()
flight_tracker = fr_api.get_flight_tracker_config()
flight_tracker.vehicles = "0"
fr_api.set_flight_tracker_config(flight_tracker)
Пулково = fr_api.get_airport('LED')
информация: dict[int, dict[str, Any]] = {}
интерес = {'number': 'Рейс', 'airline_iata': 'Авиакомпания', 'latitude': 'Широта', 'longitude': 'Долгота',
		   'heading': 'Курс', 'altitude': 'Высота', 'ground_speed': 'Скорость', 'aircraft_code': 'Тип',
		   'registration': 'Регистрационный номер', 'origin_airport_iata': 'Аэропорт отправления',
		   'destination_airport_iata': 'Аэропорт прибытия', 'get_distance_from(Пулково)': 'Расстояние до Пулково'}
превод = {'Рейс': 'Flight', 'Авиакомпания': 'Airline', 'Широта': 'Latitude', 'Долгота': 'Longitude',
		   'Курс': 'Well', 'Высота': 'Height', 'Скорость': 'Speed', 'Тип': 'Type',
		   'Регистрационный номер': 'Registration number', 'Аэропорт отправления': 'Departure airport',
		   'Аэропорт прибытия': 'Arrival airport', 'Расстояние до Пулково': 'Distance to Pulkovo'}

def fly(рейс):
	компания = str()
	for знак in рейс:
		if not знак.isdigit():
			компания += знак
	Авиакомпания = fr_api.get_flights(компания)
	for ac in Авиакомпания:
		if рейс == ac.callsign:
			самолёт: dict[str, Any] = {}
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
			информация[list(информация.keys())[-1]+1 if list(информация.keys()) else 0] = самолёт
	json = {}
	for k, v in информация.items():
		json[k] = {}
		for sk, sv in v.items():
			json[k][превод[sk]] = sv
	return dumps(json)