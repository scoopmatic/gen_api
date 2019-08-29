import json
import sys


input = json.load(open(sys.argv[1])) # Format as in example.json
output = {}

for key, value in input.items():
	if "erityistiedot" not in value:
		value["erityistiedot"] = ["noabbr"]
	if "erät" not in value:
		value["erät"] = [value['lopputulos']]

	# Synthesize final result event
	events = [{"event_idx": "E1",
        	  "Type": "Lopputulos",
       		  "Home": value['koti'],
	 	  "Guest": value['vieras'],
	          "Score": "%d–%d" % tuple(value["lopputulos"]),
        	  "Periods": '('+', '.join(["%d–%d" % tuple(period) for period in value["erät"]])+')',  #"(1–0, 1–1, 0–1, 1–0)",
	          "Abbreviations": ','.join(value["erityistiedot"]),
        	  "Time": 0.0}]

	# Syntesize other events
	game_events = []
	scores = {'koti': 0, 'vieras': 0}

	for goal in value["maalit"]:
		scores[goal["joukkue"]] += 1
		if "erityistiedot" not in goal:
			goal["erityistiedot"] = ["noabbr"]
		game_events.append({'Type': 'Maali', 
			      'Score': "%(koti)d–%(vieras)d" % scores, 
                              'Player': goal["tekijä"],
                              'Assist': ', '.join(goal["syöttäjät"]),
                              'Team': value[goal["joukkue"]],
                              'Abbreviations': ','.join(goal["erityistiedot"]),
                              'Time': float(goal["aika"].replace(':', '.')),
                              'Player_fullname': goal["tekijä"],
                              'Assist_fullname': ', '.join(goal["syöttäjät"])})

	for penalty in value["jäähyt"]:
		#  "syy": "koukkaaminen" <-- field missing in training data
		game_events.append({'Type': 'Jäähy',
			            'Player': penalty["pelaaja"],
			            "Team": value[penalty["joukkue"]],
			            "Minutes": penalty["minuutit"],
			            "Time": float(penalty["aika"].replace(':','.')),
			            "Player_fullname": penalty["pelaaja"]})


	game_events.sort(key=lambda x: x["Time"])
	for i, event in enumerate(game_events, 2):
		event['event_idx'] = 'E%d' % i
		events.append(event)
	
	# TODO: support for saves event; define API format

	output[key] = {'events': events}


json.dump(output, open(sys.argv[2], 'w'), indent=2)
