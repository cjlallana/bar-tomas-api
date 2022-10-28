from google.cloud import ndb


class Season(ndb.Model):
    name = ndb.StringProperty(required=True, indexed=True)
    current_jornada = ndb.IntegerProperty()
    last_table_check = ndb.DateTimeProperty()
    last_matches_check = ndb.DateTimeProperty()
    active = ndb.BooleanProperty(indexed=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

class Table(ndb.Model):
    standings = ndb.JsonProperty()
    jornada = ndb.IntegerProperty(indexed=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Match(ndb.Model):
    class Status:
        PENDING = 'PENDING'
        PLAYED = 'PLAYED'

    code = ndb.StringProperty(required=True, indexed=True)
    jornada = ndb.IntegerProperty(indexed=True)
    home_away = ndb.BooleanProperty()  # True=home, False=away
    team_home_name = ndb.StringProperty()
    team_away_name = ndb.StringProperty()
    field = ndb.StringProperty()
    date = ndb.DateProperty(indexed=True)
    time = ndb.StringProperty()
    weekday = ndb.StringProperty()
    team_home_goals = ndb.IntegerProperty()
    team_away_goals = ndb.IntegerProperty()
    status = ndb.StringProperty()

    def to_dict(self):
        result = super().to_dict()
        result['date'] = self.date.strftime('%d-%m-%Y')
        return result

class Player(ndb.Model):
    name = ndb.StringProperty()
    phone = ndb.StringProperty()
    email = ndb.StringProperty()

class Kid(ndb.Model):
    name = ndb.StringProperty()
    father = ndb.KeyProperty()
