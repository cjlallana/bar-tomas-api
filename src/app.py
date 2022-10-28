from datetime import datetime

# For some reason, without this import, the app doesn't find directories in src
import os
os.chdir(os.path.dirname(__file__))

# Import and initialization of Flask
from flask import Flask, render_template, request, session, redirect, jsonify
app = Flask(__name__)
app.secret_key = 'guybrush-threepwood'
logger = app.logger

from google.cloud import ndb

from .firebase_decorators_rest import auth_required

from .ffmadrid_api import _get_table_primera, _get_matches, _get_matches2

from .models import Season, Table, Match, Player, Kid

TEMP_MAIN = 'main3.html'
TEMP_LOGIN = 'login.html'

client = ndb.Client(project='bar-tomas-api')

BAR_TOMAS_CODE = 1022


# [START Firebase login/logout endpoints]

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        template_data = {'redirect_url': session.get('last_url_in_request', '/')} 
        return render_template(TEMP_LOGIN, **template_data)

    if request.method == 'POST':
        body = request.get_json()

        session['id_token'] = body.get('idToken')
        session['refresh_token'] = body.get('refreshToken')
        
        redirect_url = (
            body.get('redirect_url') if body.get('redirect_url') else '/')

        return {'msg': 'OK'}, 200

@app.route('/logout')
def logout():
    del session['id_token']
    del session['refresh_token']

    return redirect("/login", code=302)

# [END Firebase login/logout endpoints]

# [START API endpoints]

@app.route('/api/create_season')
def create_season():
    if not request.args.get('name'):
        return {'msg': 'Error creating Season. Missing "name" parameter'}, 400

    season = Season(name=request.args.get('name'))
    with client.context():
        season.put()

    return {'msg': 'Season created'}, 200

@app.route('/api/get_table')
def api_get_table():

    q = Season.query().filter(Season.active == True)
    with client.context():
        # We assume there is only one active season
        season = q.get()
        # We retrieve the last table
        table = Table.query(ancestor=season.key).order(-Table.jornada).get()

    return {
        'table': table.standings,
        'last_update': table.created,
        'last_table_check': season.last_table_check}

@app.route('/api/get_matches')
def api_get_matches():

    q = Season.query().filter(Season.active == True)
    with client.context():
        # We assume there is only one active season
        season = q.get()
        # We retrieve the matches
        #matches = Match.query(ancestor=season.key).fetch()
        matches = Match.query(ancestor=season.key).order(Match.date)

        matches_lst = [match.to_dict() for match in matches]

    return jsonify({
        'matches': matches_lst,
        'last_matches_check': season.last_matches_check})

    #return {'matches': matches}


# [END API endpoints]

# [START Flask rendered endpoints]
@app.route('/')
def get_table():

    template_data = {}

    template_data.update(api_get_table())
    template_data.update(api_get_matches().json)

    return render_template(TEMP_MAIN, **template_data)

@app.route('/get_matches')
def get_matches():

    template_data = {}

    matches, _ = api_get_matches()
    template_data.update(matches)

    return render_template(TEMP_MAIN, **template_data)

# [END Flask rendered endpoints]

# [START Internal endpoints]

@app.route('/internal/check_table')
def check_table():
    # Retrieve the current table from the FFMadrid web
    standings, current_jornada = _get_table_primera()

    # Retrieve the current season
    q = Season.query().filter(Season.active == True)
    with client.context():
        # We assume there is only one active season
        season = q.get()

    # Check if there is a table update for a new jornada
    if season:
        if season.current_jornada != current_jornada:
            # Create a new table
            table = Table(
                parent=season.key,
                standings=standings,
                jornada=current_jornada
            )
            with client.context():
                table.put()
            msg = 'New table found and created'

            season.current_jornada = current_jornada

        else:
            msg = 'No table update'

        season.last_table_check = datetime.now()
        with client.context():
            season.put()

    else:
        msg = 'No season found'

    return {'msg': msg}, 200


@app.route('/internal/check_matches')
def check_matches():
    # Retrieve the current table from the FFMadrid web
    matches = _get_matches()

    # Retrieve the current season
    q = Season.query().filter(Season.active == True)
    with client.context():
        # We assume there is only one active season
        season = q.get()
        season.last_matches_check = datetime.now()
        season.put()

    for m in matches:
        # Check if the match entity already exists
        
        with client.context():
            match = Match.query().filter(Match.code == m['code']).get()

            if not match:

                home_away = True if int(m['team_home_code']) == BAR_TOMAS_CODE else False

                match = Match(
                    parent=season.key,
                    code=m['code'],
                    jornada=int(m['jornada']),
                    home_away=home_away,
                    team_home_name=m['team_home_name'],
                    team_away_name=m['team_away_name'],
                    field=m['field'],
                    date=m['date'],
                    time=m['time'],
                    weekday=m['weekday']
                )

                if m['team_home_goals'] != '-':
                    match.status = Match.Status.PLAYED
                    match.team_home_goals = int(m['team_home_goals'])
                    match.team_away_goals = int(m['team_away_goals'])

                else:
                    match.status = Match.Status.PENDING

                match.put()
                logger.info(f'Match {m["code"]} created')

    return {'msg': 'Matches correctly checked and updated'}, 200

# [END Internal endpoints]

# [START Test endpoints]

@app.route('/test/get_table')
def test_get_table():

    standings, _ = _get_table_primera()

    return {'table': standings}, 200

@app.route('/test/get_matches')
def test_get_matches():

    matches = _get_matches()

    return {'matches': matches}, 200

@app.route('/test1')
def test1():
    return {'msg': 'hola, entrando sin login'}, 200

@app.route('/test2')
@auth_required
def test2():
    return {'msg': 'hola, entrando con login'}, 200

@app.route('/test_user')
@auth_required
def get(user):
    user_email = user.get('email')
    return {'msg': f'Correctly logged in as {user_email}'}

    print('Entering get()')

    print(user.get('email'))

    template_data = {'user_email': user.get('email')}

    return render_template(TEMP_MAIN, **template_data)


@app.route('/test_post', methods=['POST'])
@auth_required
def post():

    print(dir(request))
    return 'POST received'

@app.route('/test_ndb_create')
def test_ndb_create():

    with client.context():
        player = Player.query().get()

    # with client.context():
    #     player = Player(
    #         name="John Smith",
    #         phone="555 617 8993",
    #         email="john.smith@gmail.com")
    #     player.put()

    with client.context():
        kid = Kid(
            name="Johny Boy",
            father=player.key)
        kid.put()

    return {'msg': 'Test OK'}, 200


@app.route('/test_ndb_load')
def test_ndb_load():

    with client.context():
        player = Player.query().get()

        q = Kid.query().filter(Kid.father == player.key)
        kid = q.get()

    print(kid.father.get().phone)

    return {'msg': 'OK'}, 200

# [END Test endpoints]