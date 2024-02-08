import os
from flask import Flask, request, jsonify, make_response
from cfenv import AppEnv
from hdbcli import dbapi

app = Flask(__name__)

# assign the port that the flask application runs on
port = int(os.environ.get('PORT', 52000))


@app.route('/', methods=['GET'])
def hello():

    env = AppEnv()
    hdi_db_actionserver = env.get_service(name='hdi_db_actionserver')
    if hdi_db_actionserver is not None:
        cred = hdi_db_actionserver.credentials
        db_address = cred.get('host')
        db_port = cred.get('port')
        db_user = cred.get('user')
        db_password = cred.get('password')
        db_scheme = cred.get('schema')

        conn = dbapi.connect(
            address=db_address,
            port=db_port,
            user=db_user,
            password=db_password
        )

        db_error = ''

        try:
            sql = f'SELECT "OPERATION", "OPERATION_NAME" FROM "{db_scheme}"."Config.Operation"'
            cursor = conn.cursor()
            cursor.execute(sql)
            cursor_data = cursor.fetchall()
        except Exception as e:
            db_error = f"DB ERROR: {e}"

        cursor_string = ''

        for row in cursor_data:
            cursor_string += '\n' + str(row.column_values)

    else:
        service = ' hdi_db_actionserver is not found'
    response = make_response(f'env.name: {env.name};  env.port: {env.port}; env.space: {env.space}; service: {cred}; \n {cursor_string} \n {db_error}!')
    response.headers['Content-Type'] = 'text/plain'
    return response


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
