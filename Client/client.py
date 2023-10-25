import json, matplotlib.pyplot as plt, numpy as np
from paho.mqtt import publish, client
from flask import Flask, request as frequest
from os import urandom

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

name = "client"
with open(f'conf/{name}.json') as f:
    conf = json.load(f)
conf['run'] = 0
bank = []

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
    global name, conf, bank
    try:
        print(data)
        match data['var']:
            case "start":
                del conf['run']
                if data['params'] != "":
                    temp = json.loads(data['params'])
                    conf['params']['keep'] = temp.get('keep') if temp.get('keep') != None else conf['params']['keep']

                with open(f'conf/{name}.json', 'w') as f:
                    f.write(json.dumps(conf, indent=4))

                conf['run'] = 1
                return "Started the data collection"
            case "stop":
                conf["run"] = 0
                return "Stopped the data collection"
            case "config":
                print(conf)
                if conf['source']['method'] == 'HTTP':
                    return conf
                else:
                    publish.single(topic=conf['source']['path'], payload=json.dumps(conf), hostname=conf['source']['address'])
                    return "MQTT SENT"
            case "data":
                if conf['run'] == 1:
                    if len(bank) >= int(conf['params']['keep']):
                        bank.pop(0)
                    del data['var']
                    bank.append(data)
                return "OK"
            case "graph":
                if conf['run'] == 1:
                    key = list(json.loads(data['params']).keys())[0]
                    value = json.loads(data['params'])[key]
                    plot_values = []
                    for bank_part in bank:
                        try:
                            plot_values.append(bank_part[key][value])
                        except Exception: plot_values.append(0)

                    if data['type'] == 'line':
                        plt.clf()
                        xaxis = np.arange(1, len(plot_values) + 1, 1, dtype=int)
                        plt.plot(xaxis, plot_values)
                        plt.title(f"Line graph of {data['params']}")
                        plt.xlabel("Step")
                        plt.ylabel("Value")
                    else:
                        plt.clf()
                        plt.hist(plot_values)
                        plt.title(f"Histogram of {data['params']}")
                        plt.xlabel("Value")
                        plt.ylabel("Amount")
                    plt.savefig('graph.png', bbox_inches='tight')
                    with open('graph.png', 'rb') as f:
                        photodata = bytearray(f.read())
                    return photodata

                return "Currently nothing"
            case _:
                return "Case Default"
    except Exception: return "Error :("

@app.route('/', methods=['POST'])
def index():
    global name, conf
    data = frequest.get_json()
    return main(data)
