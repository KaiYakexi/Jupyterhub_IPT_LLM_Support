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
from jupyterhub.services.auth import HubAuth
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

auth = HubAuth(api_token=os.environ['JUPYTERHUB_API_TOKEN'], cache_max_age=60)

app = Flask(__name__)

app.secret_key = secrets.token_bytes(32)

client= OpenAI(api_key="***REMOVED***")

def sendRequestToLLM(data):
    if data['supportType']=='noSupport':
        return
    elif data['supportType']=='customPrompt':
        prompt=data['customPrompt']
    elif data['supportType']=='genericSupport':
        prompt = f"""
    How do I solve a {data['errorName']} error in Python?
    """
    elif data['supportType']=='personalizedSupport':
        prompt = f"""
    How do I solve this {data['errorName']} in Python, this is my traceback: {data['traceback']}
    and this is my source code: {data['sourceCode']}   
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
    """Decorator for authenticating with the Hub via API token"""

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

@app.route(prefix+'userSupportGroup', methods=['GET'])
@authenticated
def userSupportGroup(user):
    try:
        designatedSupportGroup='noSupport'
        if 'customPrompt' in user['groups']:
            designatedSupportGroup='customPrompt'
        elif 'genericSupport' in user['groups']:
            designatedSupportGroup='genericSupport'
        elif 'personalizedSupport' in user['groups']:
            designatedSupportGroup='personalizedSupport'
        return jsonify({
            'success': True,
            'designatedSupportGroup': designatedSupportGroup
        })
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

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


        
@app.route(prefix+'successLog', methods=['POST'])
@authenticated
def successLog(user):
    try:
        data=request.json
        print(data)
        receptionTS= datetime.datetime.now().timestamp()
        data['user']=user['name']
        data['receptionTS']=receptionTS
        db= get_db()
        db.loggedData_data.insert_one(data)
        return jsonify({'success': True, 'message': 'Data uploaded successfully'})
    except Exception as e:
        return jsonify({'success':False, 'message':str(e)})
        
@app.route(prefix+"errorLog", methods=['POST'])
@authenticated
def askLLM(user):
    try:
        data = request.json
        receptionTS= datetime.datetime.now().timestamp()
        if not data:
            return Response(
                json.dumps({'error': 'No payload received'},status=400)
            )
        LLMResponse=sendRequestToLLM(data)
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


@app.route(prefix+"errorLogBeforePrompt", methods=['POST'])
@authenticated
def errorLogBeforePrompt(user):
    try:
        data = request.json
        receptionTS= datetime.datetime.now().timestamp()
        if not data:
            return Response(
                json.dumps({'error': 'No payload received'},status=400)
            )
        sendTS=datetime.datetime.now().timestamp()
        db= get_db()
        data['user']=user['name']
        data['receptionTS']=receptionTS
        data['sendTS']=sendTS
        db=get_db()
        db.loggedData_data.insert_one(data)
        return jsonify({'success': True, 'message': 'Data uploaded successfully'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})
