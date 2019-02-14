import flask
from flask import request, Flask, make_response
import json
import traceback
import io

app=Flask(__name__)

def run_gen(lines):
    """This should return the lines translated"""
    #...do the gen here
    #return a string with the result
    return lines

@app.route("/api-v1", methods=["POST"])
def req_batch():
    json_data=request.json
    try:
        assert isinstance(json_data,dict)
        buff=io.StringIO()
        line_ids=[]
        for game_id,game_specs in json_data.items():
            home=game_specs["koti"]
            visitor=game_specs["vieras"]
            goal_h,goal_v=game_specs["lopputulos"]
            et=" ".join(game_specs.get("erityistiedot",["noabbr"]))
            print(home,visitor,"lopputulos","{}-{}".format(goal_h,goal_v),et,file=buff)
            line_ids.append(game_id)
            score=[0,0]
            for goal in game_specs.get("maalit",[]):
                lucky_guy=goal["tekijä"]
                team=goal["joukkue"]
                if team=="koti":
                    team=home
                    score[0]+=1
                else:
                    team=visitor
                    score[1]+=1
                time=goal.get("aika","")
                et=" ".join(goal.get("erityistiedot",["noabbr"]))
                print(home,visitor,"maali","{}-{}".format(*score),lucky_guy,team,time,file=buff)
                line_ids.append(game_id)
                generated=run_gen(buff.getvalue())
                result={}
                for game_id,line in zip(line_ids,generated.rstrip("\n").split("\n")):
                    result.setdefault(game_id,[]).append(line)
                return json.dumps(result,indent=4)+"\n",200,{'Content-Type': 'application/json; charset=utf-8'}
    except:
        return traceback.format_exc(),400


            

