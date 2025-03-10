from flask import Flask
# from flask.ext.cors import CORS, cross_origin
from flask import jsonify, request

import json
# from conn_opcua.conn_opcua_server import OpcuaServerConn

from settings import Settings

app = Flask(__name__)
#wp, res = genBendingResources()

@app.route('/robot_confs')
def readRobotConfs():
    
    response = jsonify(Settings.read())
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response



if __name__ == '__main__':
    
    app.run('127.0.0.1', port=5000, debug=True)