"""
askLLM service authentication with the Hub
"""

import json
import os
import secrets
from functools import wraps
from pymongo import MongoClient
from flask import Flask, Response, make_response, redirect, request, session, jsonify
from openai import OpenAI
from jupyterhub.services.auth import HubOAuth
from bson import json_util
import datetime

def get_db():
    mongoClient= MongoClient(host='mongodb',
                         port=27017, 
                         username='ranDumUs8er99991', 
                         password='randomPassWord99919',
                        authSource="admin")
    db = mongoClient['loggedData']
    return db


    
prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')

auth = HubOAuth(api_token=os.environ['JUPYTERHUB_API_TOKEN'], cache_max_age=60)

app = Flask(__name__)

app.secret_key = secrets.token_bytes(32)

client= OpenAI(api_key="***REMOVED***")

def sendRequestToLLM(execution_counter,error_name,traceback,source_code):
    prompt = f"""
I received an error while executing some Python code. Here are the details:

    Execution Counter: {execution_counter}
    Error Name: {error_name}
    Traceback:
    {traceback}

    Source Code:
    {source_code}

    Please help me identify where the issue is and how to fix it.
"""
    completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful programming assistent"},
    {"role": "user","content":prompt}
  ]
)
    return completion.choices[0].message.content

def authenticated(f):
    """Decorator for authenticating with the Hub via OAuth or API token"""

    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for a token in the session
        token = session.get('token')

        # Allow API token authentication via headers
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if token:
            user = auth.user_for_token(token)
        else:
            user = None

        if user:
            return f(user, *args, **kwargs)
        else:
            return Response('Unauthorized', status=401)

    return decorated
@app.route(prefix+'testDB', methods=['GET'])
def testDB():
    try:
        db=get_db()
        _loggedData = db.loggedData_data.find()
        loggedData = json_util.dumps(list(_loggedData))
        response={'Data': loggedData}
        return Response(
            json.dumps(response, indent=1, sort_keys=True), mimetype='application/json'
        )
    except Exception as e:
        return Response(
            json.dumps({'success': False, 'message': str(e)}, indent=1, sort_keys=True), mimetype='application/json'
        )
    finally:
        return Response(
            json.dumps({"hey":"hey"},indent=1, sort_keys=True), mimetype='application/json')
        
@app.route(prefix+'successLog', methods=['POST'])
@authenticated
def successLog(user):
    try:
        data=request.json
        db= get_db()
        result=db.loggedData_data.insert_one(data)
        return jsonify({'success': True, 'message': 'Data uploaded successfully', 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success':False, 'message':str(e)})
        
@app.route(prefix+"errorLog", methods=['POST'])
@authenticated
def askLLM(user):
    try:
        data = request.json
        receptionTS= datetime.datetime.now().timestamp()
        execution_counter=data.get('execution_counter')
        error_name=data.get('error_name')
        traceback=data.get('traceback')
        source_code=data.get('source_text')
        if not data:
            return Response(
                json.dumps({'error': 'No payload received'},status=400)
            )
        LLMResponse= sendRequestToLLM(execution_counter,error_name,traceback,source_code)
        response={'LLMResponse':LLMResponse}
        sendTS=datetime.datetime.now().timestamp()
        db= get_db()
        data['user']=user['name']
        data['receptionTS']=receptionTS
        data['sendTS']=sendTS
        data['LLMResponse']=LLMResponse
        db=get_db()
        db.loggedData_data.insert_one(data)
        return Response(
            json.dumps(response, indent=1, sort_keys=True), mimetype='application/json'
        )
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})


@app.route(prefix + 'oauth_callback')
def oauth_callback():
    code = request.args.get('code', None)
    if code is None:
        return "Forbidden", 403

    # validate state field
    arg_state = request.args.get('state', None)
    cookie_state = request.cookies.get(auth.state_cookie_name)
    if arg_state is None or arg_state != cookie_state:
        # state doesn't match
        return "Forbidden", 403

    token = auth.token_for_code(code)
    # store token in session cookie
    session["token"] = token
    next_url = auth.get_next_url(cookie_state) or prefix
    response = make_response(redirect(next_url))
    return response