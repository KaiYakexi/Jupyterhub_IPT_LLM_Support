"""
askLLM service authentication with the Hub
"""

import json
import os
import secrets
from functools import wraps
from pymongo import MongoClient
from flask import Flask, Response, make_response, redirect, request, session
from openai import OpenAI
from jupyterhub.services.auth import HubOAuth

def get_db():
    mongoClient= MongoClient(host='mongodb',
                         port=27017, 
                         username='root', 
                         password='pass',
                        authSource="admin")
    db = client=['loggedData']
    return db

try:
    db= get_db()
except Exception as e:
    print('db not found')
    
prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')

auth = HubOAuth(api_token=os.environ['JUPYTERHUB_API_TOKEN'], cache_max_age=60)

app = Flask(__name__)
# encryption key for session cookies
app.secret_key = secrets.token_bytes(32)


client= OpenAI(api_key="***REMOVED***")


# Initialize conversation history
conversation_history = [
    {"role": "system", "content": "You are a programming expert. Answer questions about programming, including debugging code and explaining errors."}
]

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
        token = session.get("token")

        # Allow API token authentication via headers
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if token:
            user = auth.user_for_token(token)
        else:
            user = None

        if user:
            return f(user, *args, **kwargs)
        else:
            return Response("Unauthorized", status=401)

    return decorated
@app.route(prefix+"testDB", methods=['GET'])
def testDB():
    db=get_db()
    response={'Important Response':"""Pymongo installed"""}
    return Response(
        json.dumps(response, indent=1, sort_keys=True), mimetype='application/json'
    )

@app.route(prefix+"successLog", methods=['POST'])
@authenticated
def successLog(user):
    print(request.get_json())
    response={'Important Response':"""Successful Log of Success which was logged as successful because it was successful to successfully log it as a success"""}
    return Response(
        json.dumps(response, indent=1, sort_keys=True), mimetype='application/json'
    )
@app.route(prefix, methods=['POST'])
@authenticated
def askLLM(user):
    data = request.get_json()
    execution_counter=data.get('execution_counter')
    error_name=data.get('error_name')
    traceback=data.get('traceback')
    source_code=data.get('source_text')
    if not data:
        return Response(
            json.dumps({'error': 'No payload received'},status=400)
        )
    #LLMResponse= sendRequestToLLM(execution_counter,error_name,traceback,source_code)
    #response={'LLMResponse':LLMResponse}
    response={'LLMResponse':"""LLM Mock Answer"""}
    return Response(
        json.dumps(response, indent=1, sort_keys=True), mimetype='application/json'
    )


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