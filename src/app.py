'''
Created on 2019-03-26

@author: Carlos Lallana
@organization: hache2i.es
'''

# Import and initialization of Flask
from flask import Flask, render_template, request, session, redirect
app = Flask(__name__)
app.secret_key = 'guybrush-threepwood'

# For some reason, without this import, the app doesn't find directories in src
import os
os.chdir(os.path.dirname(__file__))

from .firebase_decorators_rest import auth_required

from .ffmadrid_api import _get_table, _get_matches, _get_matches2

TEMP_MAIN = 'main.html'
TEMP_LOGIN = 'login.html'

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        template_data = {'redirect_url': '/'}
        return render_template(TEMP_LOGIN, **template_data)

    if request.method == 'POST':
        body = request.get_json()

        session['id_token'] = body.get('idToken')
        session['refresh_token'] = body.get('refreshToken')
        
        redirect_url = (
            body.get('redirect_url') 
            if body.get('redirect_url')
            else '/')

        return redirect(redirect_url, code=302)

@app.route('/logout')
def logout():
    del session['id_token']
    del session['refresh_token']

    return redirect("/login", code=302)

@app.route('/test1')
def test1():
    return {'msg': 'hola, entrando sin login'}, 200

@app.route('/test2')
@auth_required
def test2():
    return {'msg': 'hola, entrando con login'}, 200

@app.route('/')
@auth_required
def get(user):

    print('Entering get()')

    print(user.get('email'))

    template_data = {'user_email': user.get('email')}

    return render_template(TEMP_MAIN, **template_data)


@app.route('/', methods=['POST'])
@auth_required
def post():

    print(dir(request))
    return 'POST received'

@app.route('/get_table')
def get_table():

    standings = _get_table()

    return {'table': standings}, 200

@app.route('/get_matches')
def get_matches():

    matches = _get_matches()

    return {'matches': matches}, 200

@app.route('/get_matches2')
def get_matches2():

    matches = _get_matches2()

    return {'matches': matches}, 200