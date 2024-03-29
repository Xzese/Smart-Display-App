#!/usr/bin/env python3
import os
import requests
import dotenv
import datetime
import webbrowser
import sys
from flask import Flask, request
import threading

os.chdir(os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

app = Flask(__name__)

token_acquired = threading.Event()

@app.route('/')
def index():
    return "Authorization Server is running"

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        exchange_code_for_token(code)
        token_acquired.set()
        return 'Token acquired, shutting down server...'
    else:
        return 'Error: Code not received'

def get_access_code():
    auth_url = 'https://www.facebook.com/v19.0/dialog/oauth'
    params = {
        'client_id': os.getenv('CLIENT_ID'),
        'redirect_uri': "https://"+os.getenv('CLIENT_IP_ADDRESS')+":5000/callback",
        'state': "{st=state123abc,ds=123456789}",
        'scope':"pages_show_list,business_management,instagram_basic",
        'response_type': 'code'
    }
    authorization_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return authorization_url

def exchange_code_for_token(code):
    endpoint_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    params = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://'+os.getenv('CLIENT_IP_ADDRESS')+':5000/callback',
        'code': code
    }
    response = requests.post(endpoint_url, params=params)
    if response.status_code == 200:
        instagram_access_token = response.json()['access_token']
        expiry_date = datetime.datetime.now() + datetime.timedelta(seconds=response.json()['expires_in'])
        os.environ['LONG_ACCESS_TOKEN'] = instagram_access_token
        os.environ['LONG_ACCESS_TOKEN_EXPIRY'] = str(expiry_date)
        dotenv.set_key('.env',"LONG_ACCESS_TOKEN", instagram_access_token)
        dotenv.set_key('.env',"LONG_ACCESS_TOKEN_EXPIRY", str(expiry_date))
        return response.json()
    else:
        return 'Error: Failed to exchange authorization code for token'

def run_server():
    app.run(host=os.getenv('CLIENT_IP_ADDRESS'), debug=True, port=5000, ssl_context='adhoc')

def acquire_token():
    webbrowser.open(get_access_code(), new=1, autoraise=True)
    token_acquired.wait()  # Wait until the token is acquired
    os._exit(0)  # Terminate the program immediately without cleanup

def run_server_with_token_acquisition():
    threading.Thread(target=acquire_token).start()
    run_server()

if __name__ == "__main__":
    run_server_with_token_acquisition()