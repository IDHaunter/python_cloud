import os
from flask import Flask, request, jsonify
from cfenv import AppEnv

app = Flask(__name__)

# assign the port that the flask application runs on
port = int(os.environ.get('PORT', 52000))


# GET request /hello
@app.route('/', methods=['GET'])
def hello():
    env = AppEnv()
    hdi_db_actionserver = env.get_service(name='hdi_db_actionserver')
    if hdi_db_actionserver is not None:
        service = hdi_db_actionserver.credentials
    else:
        service = ' hdi_db_actionserver is not found'
    return f'name: {env.name};  port: {env.port}; space: {env.space}; service: {service}!'


# GET request /greet with user parameter
@app.route('/greet', methods=['GET'])
def greet():
    user = request.args.get('user', 'Guest')
    return f'Hello, {user}!'


# POST request /process
@app.route('/process', methods=['POST'])
def process():
    data = request.json  # Getting data from JSON request body
    # logic
    return jsonify({'message': 'Data processed successfully!'})


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(port=port)
