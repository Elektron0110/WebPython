from json import dump
from pprint import pprint
from typing import Any
from FlightRadar24 import FlightRadar24API, Flight
import os

fr_api = FlightRadar24API()
flight_tracker = fr_api.get_flight_tracker_config()
flight_tracker.vehicles = "0"
fr_api.set_flight_tracker_config(flight_tracker)
Пулково = fr_api.get_airport('LED')
Зона = fr_api.get_bounds_by_point(Пулково.latitude, Пулково.longitude, 5000)
самолёты: list[tuple[str, str]] = list()
информация: dict[int, dict[str, Any]] = {}
интерес = {'number': 'Рейс', 'airline_iata': 'Авиакомпания', 'latitude': 'Широта', 'longitude': 'Долгота',
		   'heading': 'Курс', 'altitude': 'Высота', 'ground_speed': 'Скорость', 'aircraft_code': 'Тип',
		   'registration': 'Регистрационный номер', 'origin_airport_iata': 'Аэропорт отправления',
		   'destination_airport_iata': 'Аэропорт прибытия', 'get_distance_from(Пулково)': 'Расстояние до Пулково'}
превод = {'Рейс': 'Flight', 'Авиакомпания': 'Airline', 'Широта': 'Latitude', 'Долгота': 'Longitude',
		   'Курс': 'Well', 'Высота': 'Height', 'Скорость': 'Speed', 'Тип': 'Type',
		   'Регистрационный номер': 'Registration number', 'Аэропорт отправления': 'Departure airport',
		   'Аэропорт прибытия': 'Arrival airport', 'Расстояние до Пулково': 'Distance to Pulkovo'}

for file in os.listdir():
	if file[-4:] == '.txt':
		run = True
		break
else:
	run = False
	print('Файл не найден.')

if run:
	while True:
		# В_Зоне = fr_api.get_flights(bounds = Зона)
		# Рейсы_в_Зоне = tuple([ac.callsign for ac in В_Зоне])
		# print(*Рейсы_в_Зоне)
		for ac in open(file).read().upper().replace(' ', '\n').replace('S7', 'SBI').split('\n'):
			компания = str()
			for знак in ac:
				if not знак.isdigit():
					компания += знак
			самолёты.append((компания, ac))
		# print([{ac if рейс == ac.callsign else ... for ac in fr_api.get_flights(компани)} for компани, рейс in самолёты])
		for компания, рейс in самолёты:
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
		break
	pprint(информация)
json = {}
for k, v in информация.items():
	json[k] = {}
	for sk, sv in v.items():
		json[k][превод[sk]] = sv
with open(f'{file[:-4]}.json', 'w') as file: dump(json, file,)