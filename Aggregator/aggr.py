import json, requests as req
from paho.mqtt import publish, client
from flask import Flask, request as frequest
from os import urandom
from threading import Event
from __thread__ import ThreadJob
from datetime import datetime as dt
from statistics import mean

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

name = "aggr"
with open(f'conf/{name}.json') as f:
    conf = json.load(f)
conf['run'] = 0
t, values, other_values, curr_time = None, {}, {}, int(dt.today().timestamp())

def on_message(client, userdata, message):
    msg = json.loads(message.payload)
    main(msg)

if conf['source']['method'] == "MQTT":
    mqttclient = client.Client(name)
    mqttclient.connect(host=conf['source']['address'], port=conf['source']['port'], keepalive=60)
    mqttclient.on_message = on_message
    mqttclient.subscribe(conf['source']['path'])
    mqttclient.loop_start()

def main(data):
    global name, conf, t, values, curr_time, other_values
    try:
        print(data)
        match data['var']:
            case "start":
                del conf['run']
                conf['dest']['method'] = data['method'] if data['method'] != "" else conf['dest']['method']
                conf['dest']['address'] = data['address'] if data['address'] != "" else conf['dest']['address']
                conf['dest']['port'] = data['port'] if data['port'] != "" else conf['dest']['port']
                conf['dest']['path'] = data['path'] if data['path'] != "" else conf['dest']['path']
                if data['params'] != "":
                    temp = json.loads(data['params'])
                    conf['dest']['params']['frequency'] = temp.get('frequency') if temp.get('frequency')  != None else conf['dest']['params']['frequency']
                    conf['dest']['params']['time'] = temp.get('time') if temp.get('time') != None else conf['dest']['params']['time']
                    conf['dest']['params']['fields'] = temp.get('fields') if temp.get('fields') != None else conf['dest']['params']['fields']
                with open(f'conf/{name}.json', 'w') as f:
                    f.write(json.dumps(conf, indent=4))

                conf['run'] = 1
                try:
                    if t == None:
                        t = ThreadJob(thread, Event(), int(conf['dest']['params']['frequency']))
                        t.start()
                    else:
                        t.frequency = int(conf['dest']['params']['frequency'])
                except Exception: return "Couldn't start the thread"
                return "Started the thread successfully"
            case "stop":
                if t != None:
                    try:
                        t.event.set()
                        t.join()
                        t = None
                        conf['run'] = 0
                    except Exception: return "Couldn't stop the thread"
                    return "OK"
                else:
                    return "Thread couldn't be stopped, because it's not running"
            case "config":
                print(conf)
                if conf['source']['method'] == 'HTTP':
                    return conf
                else:
                    publish.single(topic=conf['source']['path'], payload=json.dumps(conf), hostname=conf['source']['address'])
                    return "MQTT SENT"
            case "data":
                for key in data:
                    if key != "var":
                        other_values[key] = data[key]
                        for field in conf['dest']['params']['fields']:
                            if conf['dest']['params']['fields'][field] in data[key].keys():
                                if values.get(field) == None:
                                    values[field] = []
                                if int(dt.today().timestamp()) - int(conf['dest']['params']['time']) > curr_time:
                                    values = {}
                                    curr_time = int(dt.today().timestamp())
                                values[field].append(float(data[key][conf['dest']['params']['fields'][field]]))
                return "OK"
            case _:
                return "Case Default"
    except Exception: return "Error :("

def thread():
    global values, conf, name, other_values
    other_values[name] = {}
    for key in values:
        other_values[name][key] = mean(values[key])
    other_values['var'] = "data"
    print(other_values)
    try:
        if conf['dest']['method'] == 'HTTP':
            address = f"http://{conf['dest']['address']}:{conf['dest']['port']}/{conf['dest']['path']}"
            r = req.post(address, json=other_values)
        else:
            publish.single(topic=conf['dest']['path'], payload=json.dumps(other_values), hostname=conf['dest']['address'])
    except Exception: print("Can't connect to the destination!")

@app.route('/', methods=['POST'])
def index():
    global name, conf
    data = frequest.get_json()
    return main(data)
