import json
from paho.mqtt import publish, client
from flask import Flask, request as frequest
from os import urandom

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

name = "controller"
with open(f'conf/{name}.json') as f:
    conf = json.load(f)
conf['run'] = 0

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
    global name, conf
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
                    conf['dest']['params']['temperature'] = temp.get('temperature') if temp.get('temperature') != None else conf['dest']['params']['temperature']

                with open(f'conf/{name}.json', 'w') as f:
                    f.write(json.dumps(conf, indent=4))

                conf['run'] = 1
                return "Started the control"
            case "stop":
                conf["run"] = 0
                return "Stopped the control"
            case "config":
                print(conf)
                if conf['source']['method'] == 'HTTP':
                    return conf
                else:
                    publish.single(topic=conf['source']['path'], payload=json.dumps(conf), hostname=conf['source']['address'])
                    return "MQTT SENT"
            case "data":
                if conf['dest']['method'] == "HTTP":  
                    if conf['run'] == 1:
                        if int(data['temperature']) > int(conf['dest']['params']['temperature']): return "False"
                        else: return "True"
                    else:
                        return "False"
                else:
                    if conf['run'] == 1:
                        if int(data['temperature']) > int(conf['dest']['params']['temperature']):
                            publish.single(topic=conf['source']['path'], payload="False", hostname=conf['source']['address'])
                        else: publish.single(topic=conf['source']['path'], payload="True", hostname=conf['source']['address'])
                    else:
                        return publish.single(topic=conf['source']['path'], payload="False", hostname=conf['source']['address'])
            case _:
                return "Case Default"
    except Exception: return "Error :("

@app.route('/', methods=['POST'])
def index():
    global name, conf
    data = frequest.get_json()
    return main(data)
