import os
from io import BytesIO
from sap import xssec
from cfenv import AppEnv
from flask import Flask, request, jsonify, make_response
from hdbcli import dbapi

app = Flask(__name__)

# assign the port that the flask application runs on
port = int(os.environ.get('PORT', 52000))


@app.route('/token', methods=['GET'])
def token():
    status_code = 401
    error_txt = 'Unauthorized'

    # access_token = request.args.get('token', '')
    authorization_header = request.headers.get('Authorization')

    if authorization_header:
        access_token = authorization_header.lstrip().replace('Bearer ', '')

        try:
            env = AppEnv()
            uaa_service = env.get_service(name='UAA-service').credentials

            security_context = xssec.create_security_context(access_token, uaa_service)
            my_email = security_context.get_email()
            my_exp_date = security_context.get_expiration_date()

            status_code = 200
            error_txt = ''
            response_txt = f'email: {my_email};  exp_date: {my_exp_date}; \n \n {access_token}'
        except Exception as e:
            error_txt += f" \n\nAdditional error description: {e}"
            response_txt = error_txt
    else:
        response_txt = error_txt + "\n\nNo authorization token"

    response = make_response(response_txt)
    response.headers['Content-Type'] = 'text/plain'
    response.status_code = status_code
    return response


@app.route('/', methods=['GET'])
def hello():
    env = AppEnv()
    hdi_db_actionserver = env.get_service(name='hdi_db_actionserver')
    cursor_string = ''

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

        cursor = conn.cursor()

        update_training_status(conn, db_scheme, 1)

        db_error = ''
        cursor_data = []

        try:
            sql = f'''
            SELECT "TENANTID",
            "BOT_GUID",
            "MODEL_GUID",
            "MODEL_TYPE_ID",
            "CREATEDAT",
            "TRAINEDAT",
            "STATUS_ID",
            "LINK"
            FROM "{db_scheme}"."Nlp.Model.Training"
            '''  # "TRAINING_DATA"

            cursor.execute(sql)
            cursor_data = cursor.fetchall()
        except Exception as e:
            db_error = f"DB ERROR: {e}"

        finally:
            cursor.close()
            conn.close()

        for row in cursor_data:
            cursor_string += '\n' + str(row.column_values)

    else:
        cursor_string = ' hdi_db_actionserver is not found'

    response = make_response(
        f'env.name: {env.name};  env.port: {env.port}; env.space: {env.space}; service: {cred}; \n {cursor_string} \n {db_error}!')
    response.headers['Content-Type'] = 'text/plain'
    return response


# GET request /greet with user parameter
@app.route('/load', methods=['GET'])
def greet():
    file_link = request.args.get('link', '/assets/012F125996853000F0000003A7EE2600.txt')
    current_directory = os.getcwd()
    file_list, dir_list = get_file_list(current_directory)
    content_string = ''

    if dir_list is not None:
        for one_dir in dir_list:
            content_string = content_string + f'\n {one_dir}'

    if file_list is not None:
        for one_file in file_list:
            content_string = content_string + f'\n {one_file}'

    file_path = current_directory + f'{file_link}'
    file_content = read_file(file_path)

    env = AppEnv()
    hdi_db_actionserver = env.get_service(name='hdi_db_actionserver')

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
        db_error = update_training_file(conn, db_scheme, file_path)
    except Exception as e:
        db_error = f"DB ERROR: {e}"
    finally:
        conn.close()

    response = make_response(f'''file link is: {file_link} \n file content is: \n {file_content} \n 
    current dir is: {current_directory} \n {content_string} \n \n {db_error}''')
    response.headers['Content-Type'] = 'text/plain'
    return response


# POST request /process
@app.route('/process', methods=['POST'])
def process():
    data = request.json  # Getting data from JSON request body
    # logic
    return jsonify({'message': 'Data processed successfully!'})


def update_training_status(connection, scheme, new_status):
    cursor = connection.cursor()

    try:
        # SQL request
        sql_update_query = f"""
        UPDATE "{scheme}"."Nlp.Model.Training"
        SET "STATUS_ID" = '{new_status}',
        "TRAINEDAT" = NOW() 
        WHERE "MODEL_GUID" = '012F125996853000F0000003A7EE0300'
        """

        cursor.execute(sql_update_query)
        connection.commit()

    except Exception as e:
        print(f"DB UPDATE ERROR: {e}")

    finally:
        cursor.close()


def update_training_file(connection, scheme, file_path):
    db_error = ''
    cursor = connection.cursor()
    # Reading file contents in byte format
    with open(file_path, 'rb') as file:
        blob_data = file.read()

    # blob_data = b'Your binary data here'
    stream = BytesIO(blob_data)

    try:
        # Выполнение запроса с использованием стрима
        sql_update_query = f"""
                UPDATE "{scheme}"."Nlp.Model.Training"
                SET "TRAINED_FILE" = ?,
                "STATUS_ID" = 5 
                WHERE "MODEL_GUID" = ?
                """

        cursor.execute(sql_update_query, (stream.getvalue(), '012F125996853000F0000003A7EE0300'))

        connection.commit()

    except Exception as e:
        db_error = f"DB UPDATE ERROR: {e}"

    finally:
        cursor.close()

    return db_error


def get_file_list(directory="."):
    try:
        # Getting a list of files in a specified directory
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

        return files, directories

    except Exception as e:
        s = f"Error getting list of files: {e}"
        return [s], []


def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        s = f"Error reading file: {e}"
        return s


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(port=port)
