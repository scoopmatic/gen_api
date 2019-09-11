import flask
from flask import request, Flask, make_response
import json
import traceback
import io
import uuid
import os
import subprocess
import re

app=Flask(__name__)


def event_selector(json_data):

    #...do the gen here
    thisdir=os.path.dirname(os.path.realpath(__file__))

    filename = uuid.uuid4().hex
    with open("tmp_files/{fname}.json".format(fname=filename), "wt", encoding="utf-8") as f:
        json.dump(json_data, f)

    completed_process = subprocess.run("cat tmp_files/{json_file}.json | bash selector_pipeline.sh".format(json_file=filename), shell=True, stdout=subprocess.PIPE)

    json_text = completed_process.stdout.decode("utf-8")
    print("my out:", json_text)


def run_gen(lines):
    """This should return the lines translated"""
    #...do the gen here
    thisdir=os.path.dirname(os.path.realpath(__file__))

    filename = uuid.uuid4().hex
    with open("tmp_files/{fname}.input".format(fname=filename), "wt", encoding="utf-8") as f:
        for line in lines:
            print(line.strip(), file=f)

    subprocess.run("bash generate.sh {this} {fname}".format(this=thisdir, fname=filename), shell=True)

    gen_lines=[]
    with open("tmp_files/{fname}.output".format(fname=filename), "rt", encoding="utf-8") as f:
        for line in f:
            gen_lines.append(line.strip())

    #return a string with the result
    return gen_lines

def detokenize(text):

    text = str(text)
    text = re.sub("</?[a-z]+>", "", text)
    text = re.sub("\*\*[a-z]+\*\*", "", text)
    text = text.replace(' \u2013 ', '\u2013').replace(' ( ', ' (').replace(' ) ', ') ').replace(' , ', ', ').replace(' : ', ':').replace(' — ', '—')
    text = re.sub(r"([0-9])\s-\s([0-9])", r"\1-\2", text) # detokenize times '3 - 5 -osuman'
    text = re.sub(r"([0-9])\s-\s([a-zA-ZÅÄÖåäö\)])", r"\1 -\2", text) # detokenize times '3 - 5 -osuman'
    text = re.sub(r"([a-zA-ZåäöÅÄÖ])\s-\s([a-zA-ZÅÄÖåäö])", r"\1-\2", text) # Juha - Pekka H.
    text = text.replace(" .", ".")
    
    text = " ".join( text.split() )

    return text




def format_results_line(game_specs):

    home=game_specs["koti"]
    visitor=game_specs["vieras"]
    goal_h,goal_v=game_specs["lopputulos"]
    et=" ".join(game_specs.get("erityistiedot",[]))
    if not et:
        et=""
    else:
        et=" <abbrevs> {et} </abbrevs>".format(et=et)
    print(game_specs)
    period_scores = ["{} – {}".format(h,v) for h,v in game_specs["erät"]]
    period_scores = "( " + " , ".join(period_scores) + " )"

    formatted_lines = []

    for l in ["short", "medium", "long"]:
        formatted_lines.append("<length>{length}</length> <type>result</type> <home> {home_team} </home> <guest> {guest_team} </guest> <score> {hs} – {gs} </score> <periods> {period_scores} </periods>{abbr}".format(length=l, home_team=home, guest_team=visitor, hs=goal_h, gs=goal_v, period_scores=period_scores, abbr=et))

    return formatted_lines

def deciding(score):

    s1, s2 = score
    if s1 == s2: # tie
        return None
    loosing_score = min(s1, s2)
    if s1 == loosing_score:
        return re.compile("[0-9]+\u2013{x}".format(x=loosing_score+1))
    if s2 == loosing_score:
        return re.compile("{x}\u2013[0-9]+".format(x=loosing_score+1))

    return None


def goaltype(prev_score, current_score, final_score):
    # Identify goal types
    deciding_score_regex = deciding(final_score)
    deciding_score = False
    last_goal = "0\u20130"

    types = []

    if current_score == "0\u20131" or current_score == "1\u20130":
        types.append( "first_goal" )
    if current_score == final_score:
        types.append( "final_goal" )
    if deciding_score_regex is not None and deciding_score == False:
        if deciding_score_regex.match(current_score):
            types.append( "deciding_goal" )
            deciding_score = True
    prev_home, prev_guest = prev_score.split("\u2013")
    current_home, current_guest = current_score.split("\u2013")
    prev_home, prev_guest, current_home, current_guest = int(prev_home), int(prev_guest), int(current_home), int(current_guest)
    if current_home == current_guest: # tasoitusmaali
        types.append( "tasoitus_maali" )
    elif prev_home == prev_guest and (current_home == prev_home+1 or current_guest == prev_guest+1): # johtomaali (second part of the if statement must be redundant...)
        types.append( "leading_goal" )
    elif (current_home == prev_home and current_guest < current_home) or (current_guest == prev_guest and current_home < current_guest): # kavennusmaali
        types.append( "kavennus_maali" )
    elif (current_home == prev_home and current_guest > current_home+1) or (current_guest == prev_guest and current_home > current_guest+1): # kasvattaa johtoa
        types.append( "increase_lead_goal" )
    else: # happens few times when there is missing events in the input data
        pass
    if types:
        types = " <goaltype> " + ", ".join(types) + " </goaltype>"
    else:
        types = None

    return types


def format_goal_line(home, visitor, total_score, current_score, goal_specs):

    # <length>medium</length> <type>goal</type> <team> Pelicans **home** </team> <player> Tommi Hannus </player> <assist> Lasse Jämsen </assist> <team_score>4</team_score> <score> 4 – 3 </score> <exact_time> 62.31 </exact_time> <approx_time>1/4</approx_time> <period>4</period> <goaltype> final_goal , deciding_goal , leading_goal </goaltype> <abbrevs> yv </abbrevs>

    lucky_guy=goal_specs["tekijä"]
    assist = goal_specs.get("syöttäjät", None)
    if assist:
        assist = " , ".join(assist)
    team=goal_specs["joukkue"]
    prev_score = "{}\u2013{}".format(current_score[0], current_score[1])
    if team=="koti":
        team=home + " **home**"
        current_score[0]+=1
        team_score = current_score[0]
    else:
        team=visitor + " **guest**"
        current_score[1]+=1
        team_score = current_score[1]
    exact_time=goal_specs.get("aika","").replace(":", ".")
    et=" ".join(goal_specs.get("erityistiedot",[]))
    if not et:
        et=""
    else:
        et = " <abbrevs> {abbr} </abbrevs>".format(abbr=et)

    # TODO
    goal_type = goaltype(prev_score, "{}–{}".format(current_score[0], current_score[1]), total_score)

    approx_time = str(int( ( ( float(exact_time)%20 ) //5 ) +1 )) +"/4"

    period = int(float(exact_time)//20+1)

    formatted_lines = []

    for l in ["short", "medium", "long"]:
        formatted = "<length>{length}</length> <type>goal</type> <team> {team} </team> <player> {player} </player> <assist> {assist} </assist> <team_score>{team_score}</team_score> <score> {hs} – {gs} </score> <exact_time> {exact_time} </exact_time> <approx_time>{approx_time}</approx_time> <period>{period}</period>".format(length=l, team=team, player=lucky_guy, assist=assist, team_score=team_score, hs=current_score[0], gs=current_score[1], exact_time=exact_time, approx_time=approx_time, period=period)
        if goal_type:
            formatted = formatted + goal_type
        formatted = formatted + et
        formatted_lines.append(formatted)

    # <goaltype> {goal_type} </goaltype> <abbrevs> yv </abbrevs>"

    # approx_time, period, goaltype
    

    return formatted_lines, current_score



@app.route("/api-v1", methods=["POST"])
def req_batch():
    json_data=request.json
    try:

        event_selector(json_data)
        print(json_data)

        assert isinstance(json_data,dict)
        buff=io.StringIO()
        line_ids=[]
        for game_id,game_specs in json_data.items():
            home=game_specs["koti"]
            visitor=game_specs["vieras"]
            total_score=game_specs["lopputulos"]
            formatted_input=format_results_line(game_specs)
            for input_ in formatted_input:
                print(input_,file=buff)
                line_ids.append(game_id)
            current_score=[0,0]
            for goal_specs in game_specs.get("maalit",[]):

                formatted_input, current_score = format_goal_line(home, visitor, total_score, current_score, goal_specs)
                for input_ in formatted_input:
                    print(input_,file=buff)
                    line_ids.append(game_id)
        buff.seek(0)
        generated=run_gen(buff)
        result={}
        for game_id,line in zip(line_ids,generated):
            detokenized = detokenize(line)
            result.setdefault(game_id,[]).append(detokenized)
        return json.dumps(result,indent=4)+"\n",200,{'Content-Type': 'application/json; charset=utf-8'}
    except:
        return traceback.format_exc(),400


            

