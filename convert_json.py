import json
import sys


input = json.load(open(sys.argv[1])) # Format as in example.json
output = {}

for key, value in input.items():
	if "erityistiedot" not in value:
		value["erityistiedot"] = ["noabbr"]

	# Synthesize final result event
	events = ["event_idx": "E1",
        	  "Type": "Lopputulos",
       		  "Home": value['koti'],
	 	  "Guest": value['vieras'],
	          "Score": "%d–%d" % tuple(value["lopputulos"]),
        	  "Periods": '('+', '.join(["%d–%d" % tuple(period) for period in value["erät"]])+')',  #"(1–0, 1–1, 0–1, 1–0)",
	          "Abbreviations": ','.join(value["erityistiedot"]),
        	  "Time": 0.0]

	# Syntesize other events
	# TODO: build goal events, penalty events, save events; sort event list by time (saves last)

	output[game] = {'events': events}


json.dump(output, open(sys.argv[2], 'w'))
