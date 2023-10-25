import json, requests as req
from paho.mqtt import publish, client
from flask import Flask, request as frequest
from os import urandom
from threading import Event
from __thread__ import ThreadJob

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

name = "source3"
with open(f'conf/{name}.json') as f:
    conf = json.load(f)
conf['run'] = 0
t, values, file = None, {}, None

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
    global name, conf, t, values, file
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
                    conf['dest']['params']['file'] = temp.get('file') if temp.get('file') != None else conf['dest']['params']['file']

                if (file != None):
                    file.close()
                    file = None
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
                        file.close()
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
    global values, file, conf, name
    if file == None:
        file = open(f"files/{conf['dest']['params']['file']}")
    values = json.loads(file.readline().replace('\n', '').replace('\'', '"'))
    print(values)

    try:
        if conf['dest']['method'] == 'HTTP':
            address = f"http://{conf['dest']['address']}:{conf['dest']['port']}/{conf['dest']['path']}"
            r = req.post(address, json={name: values, "var": "data"})
        else:
            publish.single(topic=conf['dest']['path'], payload=json.dumps({name: values, "var": "data"}), hostname=conf['dest']['address'])
    except Exception:print("Can't connect to the destination!")

@app.route('/', methods=['POST'])
def index():
    global name, conf
    data = frequest.get_json()
    return main(data)
