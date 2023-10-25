import json, requests as req, shutil
from paho.mqtt import subscribe, publish
from flask import Flask, request as frequest, render_template, send_file
from os import urandom

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800
app = Flask(__name__)
app.config.update(SECRET_KEY=urandom(24))
app.config.from_object(__name__)

with open('loc.json') as f:
    loc = json.load(f)

def site_template(x):
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Index</title>
            <link rel="stylesheet" href="https://unpkg.com/98.css">
        </head>
        <body style="background-color:#c0c0c0;">
            <div class="window" style="width: 400px">
                <div class="title-bar">
                    <div class="title-bar-text">Configuration Panel</div>
                    <div class="title-bar-controls">
                        <button aria-label="Minimize"></button>
                        <button aria-label="Maximize"></button>
                        <button aria-label="Close"></button>
                    </div>
                </div>
                <div class="window-body">
                    <pre>{x}</pre>
                </div>
            </div>
        </body>
        </html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/start', methods=['GET', 'POST'])
def start():
    if frequest.method == "GET": return render_template('start.html')
    else:
        global loc
        data = {}
        data['name'] = frequest.form.get('name')
        data['method'] = frequest.form.get('method')
        data['address'] = frequest.form.get('address')
        data['port'] = frequest.form.get('port')
        data['path'] = frequest.form.get('path')
        data['params'] = frequest.form.get('params')
        data['var'] = 'start'
        print(data)
        if data['name'] in loc.keys():
            if loc[data['name']]['method'] == 'HTTP':
                try:
                    address = f"http://{loc[data['name']]['address']}:{loc[data['name']]['port']}/{loc[data['name']]['path']}"
                    r = req.post(address, json=data)
                except Exception: return site_template(f"Couldn't post a start signal to {data['name']} with HTTP")
            else:
                try:
                    publish.single(topic=loc[data['name']]['path'], payload=json.dumps(data), hostname=loc[data['name']]['address'])
                except Exception: return site_template(f"Couldn't post a start signal to {data['name']} with MQTT")
        else: return site_template(f"No connection configuration found to {data['name']}")
        return site_template("OK")

@app.route('/stop', methods=['GET', 'POST'])
def stop():
    if frequest.method == "GET": return render_template('stop.html')
    else:
        global loc
        data = {}
        data['name'] = frequest.form.get('name')
        data['var'] = 'stop'
        print(data)
        if data['name'] in loc.keys():
            if loc[data['name']]['method'] == 'HTTP':
                try:
                    address = f"http://{loc[data['name']]['address']}:{loc[data['name']]['port']}/{loc[data['name']]['path']}"
                    r = req.post(address, json=data)
                except Exception: return site_template(f"Couldn't post a stop signal to {data['name']} with HTTP")
            else:
                try:
                    publish.single(topic=loc[data['name']]['path'], payload=json.dumps(data), hostname=loc[data['name']]['address'])
                except Exception: return site_template(f"Couldn't post a stop signal to {data['name']} with MQTT")
        else: return site_template(f"No connection configuration found to {data['name']}")
        return site_template("OK")

@app.route('/add', methods=['GET', 'POST'])
def add():
    if frequest.method == "GET": return render_template('add.html')
    else:
        global loc
        data = {}
        data['name'] = frequest.form.get('name')
        data['method'] = frequest.form.get('method')
        data['address'] = frequest.form.get('address')
        data['port'] = frequest.form.get('port')
        data['path'] = frequest.form.get('path')

        loc[data['name']] = {
            "method": data['method'],
            "address": data['address'],
            "port": data['port'],
            "path": data['path']
        }

        try:
            with open('loc.json', 'w') as f:
                f.write(json.dumps(loc, indent=4))
        except Exception: return site_template("Couldn't add a new connection, or change parameters of an existing connection")
        return site_template("OK")

@app.route('/config', methods=['GET', 'POST'])
def config():
    configdict = {}
    for conn in loc.keys():
        try:
            data = {'var': 'config'}
            if loc[conn]['method'] == 'HTTP':
                address = f"http://{loc[conn]['address']}:{loc[conn]['port']}/{loc[conn]['path']}"
                r = req.post(address, json=data)
                configdict[conn] = r.json()
            else:
                publish.single(topic=loc[conn]['path'], payload=json.dumps(data), hostname=loc[conn]['address'])
                msg = subscribe.simple(topics=f"{loc[conn]['path']}/config", hostname=loc[conn]['address'])
                configdict[conn] = json.loads(msg.payload)
        except Exception: pass
    return site_template(json.dumps(configdict, indent=4))

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    if frequest.method == "GET": return render_template('graph.html')
    else:
        global loc
        data = {}
        data['name'] = frequest.form.get('name')
        data['params'] = frequest.form.get('params')
        data['type'] = frequest.form.get('type')
        data['var'] = 'graph'
        if data['name'] in loc.keys():
            if loc[data['name']]['method'] == 'HTTP':
                try:
                    address = f"http://{loc[data['name']]['address']}:{loc[data['name']]['port']}/{loc[data['name']]['path']}"
                    r = req.post(address, json=data, stream=True)
                    with open('graph.png', 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                    return send_file('graph.png', mimetype='image/png')
                except Exception: return site_template(f"Couldn't get the graph from {data['name']} with HTTP")
            else:
                try:
                    publish.single(topic=loc[data['name']]['path'], payload=json.dumps(data), hostname=loc[data['name']]['address'])
                    msg = subscribe.simple(topics=f"{loc[data['name']]['path']}/graph", hostname=loc[data['name']]['address'])
                    with open('graph.png', 'wb') as f:
                        f.write(msg.payload)
                    return send_file('graph.png', mimetype='image/png')
                except Exception: return site_template(f"Couldn't get the graph from {data['name']} with MQTT")
        else: return site_template(f"No connection configuration found to {data['name']}")