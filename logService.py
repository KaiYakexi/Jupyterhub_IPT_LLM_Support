"""
askLLM service authentication with the Hub
"""

import json
import os
import secrets
from functools import wraps
from pymongo import MongoClient
from flask import Flask, Response, make_response, redirect, request, session, jsonify, render_template
from openai import OpenAI
from jupyterhub.services.auth import HubAuth, HubOAuth
from bson import json_util
import datetime
import requests
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from string import Template
from pathlib import Path





from solutions import SOLUTIONS

TEMPLATE_DIR=Path("prompts")
promptTemplates= {}


def load_prompt_templates():
    for path in TEMPLATE_DIR.glob("*.md"):
        with path.open(encoding="utf-8") as f:
            promptTemplates[path.stem] = Template(f.read())
            
load_prompt_templates()
#
#
#
# Uncomment the first JUPYTERHUB_URL declaration and comment out the second
# for local deployment

#JUPYTERHUB_URL = 'http://host.docker.internal:8000/jupyterhub/hub'
JUPYTERHUB_URL="$JUPYTERHUB_URL"
client= OpenAI(api_key="$OPENAI_API_KEY")
#
#
#
def get_db():
    mongoClient= MongoClient(host='mongodb',
                         port=27017, 
                         username='$MONGO_INITDB_ROOT_USERNAME', 
                         password='$MONGO_INITDB_ROOT_PASSWORD',
                        authSource="admin")
    db = mongoClient['loggedData']
    return db
    
prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')

auth = HubAuth(api_token=os.environ['JUPYTERHUB_API_TOKEN'], cache_max_age=60)
oauth = HubOAuth(api_token=os.environ['JUPYTERHUB_API_TOKEN'], cache_max_age=60)

#HEADERS = {'Authorization': 'token '}

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3, x_proto=3,x_host=3,x_prefix=3 )
app.secret_key = secrets.token_bytes(32)




def genericPrompt(data):
    return f"How do I solve a {data['errorName']} error in Python?"

def personalizedPrompt(data):
    return f"""How do I solve this {data['errorName']} in Python,
     this is my traceback: {data['traceback']} 
    and this is my source code: {data['sourceCode']}"""

def customPrompt(data):
    return f"""{data['customPrompt']}+{data['sourceCode']}+{data['traceback']}"""

# Max hints before giving out the solution (starting from 0)
maxHints=3

def instructionalTextPrompt(data):
    hintCounter=data['hintCounter']
    if int(hintCounter) < maxHints:
        templateName="instructionalHint"+str(hintCounter)+"Template"
        templateForPrompt= promptTemplates[templateName]
        return templateForPrompt.substitute(sourceCode=data['sourceCode'],traceback=data['traceback'],taskDescription=data['taskDescription'])
    return None

def workedExamplePrompt(data):
    hintCounter=data['hintCounter']
    if int(hintCounter) < maxHints:
        templateName="workedExampleHint"+str(hintCounter)+"Template"
        templateForPrompt= promptTemplates[templateName]
        return templateForPrompt.substitute(sourceCode=data['sourceCode'],traceback=data['traceback'],taskDescription=data['taskDescription'])
    return None



promptHandlers = {
    "genericSupport": genericPrompt,
    "personalizedSupport": personalizedPrompt,
    "customPrompt":customPrompt,
    "instructionalText":instructionalTextPrompt,
    "workedExample":workedExamplePrompt
}



def sendRequestToLLM(data):
    supportType=data.get("supportType")
    if supportType=='noSupport':
        return None,None
    
    handler = promptHandlers.get(supportType)
    if not handler:
        raise ValueError(f"Unknown supportType {supportType}")
    prompt=handler(data)
    if prompt is None:
        return 'Solution by teacher',SOLUTIONS[data["cellIdentifier"]]
    response = client.responses.create(
    model="gpt-4.1",
    input=[
        {"role": "system", "content": "You are a helpful programming assistant"},
        {"role": "user", "content": prompt}
    ])
    if supportType=='workedExample':
        # Turn response into markdown code block
        responseText=f"""```python\n{response.output_text}\n```"""
        return prompt,responseText
    return prompt,response.output_text

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


def oauthenticated(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get("token")

        if token:
            user = oauth.user_for_token(token)
        else:
            user = None

        if user:
            return f(user, *args, **kwargs)
        else:
            # redirect to login url on failed oauth
            state = oauth.generate_state(next_url=request.path)
            response = make_response(redirect(oauth.login_url + f'&state={state}'))
            response.set_cookie(oauth.state_cookie_name, state)
            return response

    return decorated

@app.route(prefix + 'oauth_callback')
def oauth_callback():
    code = request.args.get('code', None)
    if code is None:
        return "Forbidden", 403

    # validate state field
    arg_state = request.args.get('state', None)
    cookie_state = request.cookies.get(oauth.state_cookie_name)
    if arg_state is None or arg_state != cookie_state:
        # state doesn't match
        return "Forbidden", 403

    token = oauth.token_for_code(code)
    # store token in session cookie
    session["token"] = token
    next_url = oauth.get_next_url(cookie_state) or prefix
    response = make_response(redirect(next_url))
    return response

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
@oauthenticated
def testDB(user):
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
        promptUsed,LLMResponse=sendRequestToLLM(data)
        data['promptUsed']=promptUsed
        response={'LLMResponse':LLMResponse}
        sendTS=datetime.datetime.now().timestamp()
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


#def get_groups():
#    response = requests.get(f'{JUPYTERHUB_URL}/api/groups', headers=HEADERS)
#    response.raise_for_status()
#    return response.json()

#def get_group_roles(group_name):
#    """Get roles assigned to a group."""
#    response = requests.get(f'{JUPYTERHUB_URL}/api/groups/{group_name}/', headers=HEADERS)
#    response.raise_for_status()
#    data=response.json
#    return [data]

#def update_group_roles(group_name, new_roles):
#    """Update the roles assigned to a group."""
#    data = {'roles': new_roles}
#    response = requests.delete(
#        f'{JUPYTERHUB_URL}/api/groups/{group_name}/users',
#        headers=HEADERS,
#        json=data
#    )
#    response.raise_for_status()

#@app.route(prefix+"changeRole", methods=['GET'])
#def changeRole():
#    groups = get_groups()
#    return jsonify({'success': True, 'current':groups,'message': 'Data uploaded successfully'})

@app.route(prefix, methods=['GET'])
@oauthenticated
def adminPage(user):
    return render_template('index.html')


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
