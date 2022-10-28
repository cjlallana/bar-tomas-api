from .app import app


@app.route('/api/get_table')
def get_table():

    q = Season.query().filter(Season.active == True)
    with client.context():
        # We assume there is only one active season
        season = q.get()
        # We retrieve the last table
        table = Table.query(ancestor=season.key).order(-Table.jornada).get()

    return {'table': table.standings}, 200
