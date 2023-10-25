import json, requests as req
from paho.mqtt import publish, client, subscribe
from flask import Flask, request as frequest
from os import urandom
from threading import Event
from __thread__ import ThreadJob

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

name = "csource"
with open(f'conf/{name}.json') as f:
    conf = json.load(f)
conf['run'] = 0
t, values = None, {}

temperature = 0
tempo = 0.0
cw = 4200
run = False

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
    global name, conf, t, values
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
                    conf['dest']['params']['power'] = temp.get('power') if temp.get('power') != None else conf['dest']['params']['power']
                    conf['dest']['params']['controller'] = temp.get('controller') if temp.get('controller') != None else conf['dest']['params']['controller']

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
            case _:
                return "Case Default"
    except Exception: return "Error :("

def thread():
    global values, conf, name, temperature, tempo, cw, run
    tempo += 0.1 * int(conf['dest']['params']['frequency']) if run else -0.1 * int(conf['dest']['params']['frequency'])
    if tempo > 1: tempo = 1
    elif tempo < -0.5: tempo = -0.5

    temperature += (tempo * int(conf['dest']['params']['frequency']) * int(conf['dest']['params']['power'])) / cw
    if temperature < 0: temperature = 0
    values = {'temperature': temperature}
    print(values)

    try:
        if conf['dest']['params']['controller']['method'] == 'HTTP':
            address = f"http://{conf['dest']['params']['controller']['address']}:{conf['dest']['params']['controller']['port']}/{conf['dest']['params']['controller']['path']}"
            r = req.post(address, json={'temperature': temperature, 'var': 'data'})
            run = True if r.text == "True" else False
        else:
            publish.single(topic=conf['dest']['params']['controller']['path'], payload=json.dumps(values), hostname=conf['dest']['params']['controller']['address'])
            msg = subscribe.simple(topics=conf['dest']['params']['controller']['path'], hostname=conf['dest']['params']['controller']['address'])
            run = bool(msg.payload)
    except Exception: print("Can't connect to the controller")

    try:
        if conf['dest']['method'] == 'HTTP':
            address = f"http://{conf['dest']['address']}:{conf['dest']['port']}/{conf['dest']['path']}"
            r = req.post(address, json={name: values, "var": "data"})
        else:
            publish.single(topic=conf['dest']['path'], payload=json.dumps({name: values, "var": "data"}), hostname=conf['dest']['address'])
    except Exception: print("Can't connect to the destination!")

@app.route('/', methods=['POST'])
def index():
    global name, conf
    data = frequest.get_json()
    return main(data)
