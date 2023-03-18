
import json
from six.moves.urllib.request import urlopen
from functools import wraps

from flask import Flask, request, jsonify, _request_ctx_stack
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import cross_origin
from jose import jwt
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_ALL, 'nl_NL.utf-8')
import pytz

AUTH0_DOMAIN = 'dev-2bt0elbw.us.auth0.com'
API_AUDIENCE = 'https://appartementen-albir.nl/api'
ALGORITHMS = ["RS256"]

DB_NAME = 'albir'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'admin'
DB_PASSWORD = 'admin'
TABLE_NAME = 'bookings'

price_class_mapping = {
  'estrella': 1,
  'orly': 1,
  'bulevard': 1,
  'albimar': 1,
  'primavera': 1,
  'finplaya': 2,
  'mistral': 2
}

appartment_mapping = {
    'estrella': 'Estrella',
    'albimar': 'Albimar',
    'bulevard': 'Bulevard',
    'finplaya': 'Fin Playa',
    'mistral': 'Mistral',
    'primavera': 'Primavera',
    'orly': 'Orly'
}

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# CREATE TABLE `albir`.`bookings` (
#   `id` INT NOT NULL,
#   `appartment_id` VARCHAR(45) NOT NULL,
#   `name` VARCHAR(255) NOT NULL,
#   `arrival` DATE NOT NULL,
#   `departure` DATE NOT NULL,
#   `email` VARCHAR(255) NULL,
#   `phone` VARCHAR(20) NULL,
#   `portal` VARCHAR(45) NOT NULL,
#   `total` DOUBLE NULL,
#   `deposit` DOUBLE NULL,
#   `total_made` TINYINT NOT NULL,
#   `deposit_made` TINYINT NOT NULL,
#   `remarks` LONGTEXT NULL,
#   PRIMARY KEY (`id`));

class Booking(db.Model):

    __tablename__ = TABLE_NAME

    id = db.Column(db.Integer(), primary_key=True)
    appartment_id = db.Column(db.String(45), nullable=False)
    name = db.Column(db.String(45), nullable=False)
    arrival  = db.Column(db.Date(), nullable=False)
    departure = db.Column(db.Date(), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    portal = db.Column(db.String(45), nullable=False)
    total = db.Column(db.Float(), nullable=True)
    deposit = db.Column(db.Float(), nullable=True)
    total_made = db.Column(db.Integer(), nullable=False)
    deposit_made = db.Column(db.Integer(), nullable=False)
    remarks = db.Column(db.Text(), nullable=True)

# CREATE TABLE `albir`.`prices` (
#   `id` INT NOT NULL AUTO_INCREMENT,
#   `price_class` INT NOT NULL,
#   `year` INT NOT NULL,
#   `month` INT NOT NULL,
#   `price` DOUBLE NULL,
#   PRIMARY KEY (`id`));

class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer(), primary_key=True)
    price_class = db.Column(db.Integer(), nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    month = db.Column(db.Integer(), nullable=False)
    price = db.Column(db.Integer(), nullable=True)

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)

    token = parts[1]
    return token

def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer="https://"+AUTH0_DOMAIN+"/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    "please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                        "description": "Unable to find appropriate key"}, 401)
    return decorated

def requires_scope(required_scope):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    app.logger.info(unverified_claims)
    if unverified_claims.get("permissions"):
            # token_scopes = unverified_claims["scope"].split()
            token_scopes = unverified_claims["permissions"]
            for token_scope in token_scopes:
                if token_scope == required_scope:
                    return True
    return False

# For mm-planning
import pandas as pd
from csv import reader
import unicodedata

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode()

month_parser = {
    'jan': 1,
    'feb': 2,
    'mrt': 3,
    'apr': 4,
    'mei': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'okt': 10,
    'nov': 11,
    'dec': 12
}

surveyors = [
    'Titus van der Zee',
    'Govert Wesseling',
    'Bert van Angeren',
    'Andre Loeve',
    'Robin Stadt',
    'Mark van Vliet',
    'Willem van Opstal'
]

url_q1 = "https://docs.google.com/spreadsheets/d/1BdDjmZIlnlKC86HdS5OIiTg0zfxy8bogPCmsN--sdYo/gviz/tq?tqx=out:csv"
url_q2 = "https://docs.google.com/spreadsheets/d/12NhhiEeVsZhlX2axM-RsF9YPxAWWIKDdr3zAQOS0eeg/gviz/tq?tqx=out:csv"
url_q3 = "https://docs.google.com/spreadsheets/d/19BriryfA7TjrxXwALM10TckAfamKXL84YKqVWpPZaaE/gviz/tq?tqx=out:csv"
url_q4 = "https://docs.google.com/spreadsheets/d/18zRt9fJoW7eZMf8gBy5lSOzxwGAgGYJejk50UJFr_MA/gviz/tq?tqx=out:csv"
first_day_in_header = 4
first_day_in_sheet = 3

@app.route("/api/mm-planning")
@cross_origin(headers=["Content-Type", "Authorization"])
def public_planning():

    surveyor_index = {}
    per_surveyor = {}
    vessels = ['Arca', 'Zirfaea']
    vessel_index = {}
    vessel_per_date = {}
    per_vessel = {}


    for url in [url_q1, url_q2]:#, url_q3, url_q4]:
        first_date_of_this_sheet = None

        print(url)

        df = pd.read_csv(url)
        csv = df.to_csv()
        csvl = csv.split("\n")

        for l, line in enumerate(csvl):
            sline = line.split(',')
            if sline[1] == "Support":
                break
            if not first_date_of_this_sheet:
                first_date_of_this_sheet = datetime.strptime(f"{sline[1][:4]}-{month_parser[sline[first_day_in_header].split(' ')[2]]}-{sline[first_day_in_header].split(' ')[1]}", "%Y-%m-%d").date()
            if remove_accents(sline[1]) in surveyors:
                surveyor_index[sline[1]] = l
            if remove_accents(sline[1]) in vessels:
                vessel_index[sline[1]] = l

        for vessel, vindex in vessel_index.items():
            # print('---------\n', vindex, vessel)
            if vessel not in per_vessel:
                per_vessel[vessel] = []
            sdp = csvl[vindex].split(',')
            sd = []
            part = ""
            opened = False
            for s, sss in enumerate(sdp):
                if '"' in sss and not opened:
                    opened = True
                    part += sss
                elif '"' in sss and opened:
                    opened = False
                    part += sss
                    sd.append(part)
                    part = ""
                elif opened:
                    part += ""
                else:
                    sd.append(sss)
            sd = sd[first_day_in_sheet:]
            # print(sd)
            current_date = first_date_of_this_sheet
            ci = 0

            event = {'start': current_date, 'end': current_date, 'occupance': None, 'theme': None}

            while ci < len(sd):

                if "Samenvatting" in sd[ci]:
                    break

                note = sd[ci + 0]
                occupance = sd[ci + 1].split(' ')[0]
                theme = sd[ci + 2]

                # print(f"{ci}: {current_date} - {note} - {occupance} - {theme}")

                if occupance == event.get('occupance') and theme == event.get('theme'):
                    event['end'] = current_date
                else:
                    if event.get('occupance') or event.get('theme'):
                        event['start'] = datetime.strftime(event['start'], "%Y-%m-%d")
                        event['end'] = datetime.strftime(event['end'], "%Y-%m-%d")
                        per_vessel[vessel].append(event)
                    event = {'start': current_date, 'end': current_date, 'occupance': occupance, 'theme': theme}

                if theme:
                    if current_date not in vessel_per_date.keys():
                        vessel_per_date[current_date] = {theme: vessel}
                    else:
                        vessel_per_date[current_date][theme] = vessel

                ci += 3
                current_date += timedelta(days = 1)

            if event.get('occupance') or event.get('theme'):
                event['start'] = datetime.strftime(event['start'], "%Y-%m-%d")
                event['end'] = datetime.strftime(event['end'], "%Y-%m-%d")
                per_vessel[vessel].append(event)

        for surveyor, sindex in surveyor_index.items():
            # print(f"------------\n{surveyor}")

            if remove_accents(surveyor.split(' ')[0]) not in per_surveyor:
                per_surveyor[remove_accents(surveyor.split(' ')[0])] = []
            sdp = csvl[sindex].split(',')
            sd = []
            part = ""
            opened = False
            for s, sss in enumerate(sdp):
                if '"' in sss and not opened:
                    opened = True
                    part += sss
                elif '"' in sss and opened:
                    opened = False
                    part += sss
                    sd.append(part)
                    part = ""
                elif opened:
                    part += ""
                else:
                    sd.append(sss)
            sd = sd[first_day_in_sheet:]
            # print(sd)
            current_date = first_date_of_this_sheet
            ci = 0

            event = {'start': current_date, 'end': current_date, 'vessel': None, 'theme': None, 'work': None}

            while ci < len(sd):
                if "Samenvatting" in sd[ci]:
                    break

                note = sd[ci + 0]
                work = sd[ci + 1]
                theme = sd[ci + 2]

                try:
                    vessel = vessel_per_date.get(current_date).get(theme)
                except:
                    vessel = None

                # print(f"{ci}: {current_date} - {note} - {work} - {theme} - {vessel}")

                if work == event.get('work') and theme == event.get('theme') and vessel == event.get('vessel'):
                    event['end'] = current_date
                else:
                    if event.get('work') or event.get('theme') or event.get('vessel') and event.get('work') != 'Afwezig':
                        if 'Kantoor' in event.get('work'):
                            event['work'] = "Kantoor"
                        event['start'] = datetime.strftime(event['start'], "%Y-%m-%d")
                        event['end'] = datetime.strftime(event['end'], "%Y-%m-%d")
                        per_surveyor[remove_accents(surveyor.split(' ')[0])].append(event)
                    event = {'start': current_date, 'end': current_date, 'vessel': vessel, 'theme': theme, 'work': work}


                ci += 3
                current_date += timedelta(days = 1)

            if event.get('work') or event.get('theme') or event.get('vessel') and event.get('work') != 'Afwezig':
                if 'Kantoor' in event.get('work'):
                    event['work'] = "Kantoor"
                event['start'] = datetime.strftime(event['start'], "%Y-%m-%d")
                event['end'] = datetime.strftime(event['end'], "%Y-%m-%d")
                per_surveyor[remove_accents(surveyor.split(' ')[0])].append(event)

    response = {'vessels': per_vessel, 'surveyors': per_surveyor}
    return jsonify(response)

# This doesn't need authentication
@app.route("/api/test")
@cross_origin(headers=["Content-Type", "Authorization"])
def public():
    response = get_prices()
    return jsonify(message=response)

def format_date(obj):
    return datetime.strftime(obj, "%Y-%m-%d")

def format_appartment_from_id(app):
    return appartment_mapping.get(app, 'Onbekend')

def get_prices(calendar=False):
    prices = Price.query.order_by(Price.price_class, Price.year, Price.month).all()
    price_dict = {}
    for p in prices:
        if p.price_class not in price_dict:
            price_dict[p.price_class] = {}

        if p.year not in price_dict[p.price_class]:
            price_dict[p.price_class][p.year] = [p.price]
        else:
            price_dict[p.price_class][p.year].append(p.price)
    return price_dict

def get_availability(appartment_id):
    array = []
    today = datetime.now(pytz.timezone('Europe/Amsterdam')).date()
    min_date = today - timedelta(days=60)
    bookings = Booking.query.filter(Booking.appartment_id == appartment_id, Booking.arrival >= datetime.strftime(min_date, "%Y-%m-%d")).order_by(Booking.arrival).all()
    for b in bookings:
        unavailable_day = b.arrival
        while unavailable_day <= b.departure:
            array.append(datetime.strftime(unavailable_day, "%Y-%m-%d"))
            unavailable_day += timedelta(days=1)
    return array

def get_bookings_for_dashboard():
    dashboard_data = {
        'upcoming': {
            'Albimar': [],
            'Estrella': [],
            'Bulevard': [],
            'Fin Playa': [],
            'Mistral': [],
            'Primavera': [],
            'Orly': []
        },
        'bookings': {},
        'last_id': db.session.query(func.max(Booking.id)).scalar(),
        'prices': get_prices(),
        'price_class_mapping': price_class_mapping
    }

    today = datetime.now(pytz.timezone('Europe/Amsterdam')).date()
    upcoming = today + timedelta(days=15)
    print('fetching bookings..')
    # bookings = Booking.query.filter(Booking.departure >= datetime.strftime(today, "%Y-%m-%d")).order_by(Booking.appartment, Booking.arrival).all()
    bookings = Booking.query.order_by(Booking.appartment_id, Booking.arrival).all()
    active_appartment = None

    for b in bookings:
        if b.appartment_id != active_appartment:
            if active_appartment:
                dashboard_data['upcoming'][format_appartment_from_id(active_appartment)] = active_upcoming_list
            active_appartment = b.appartment_id
            last_occupied = today - timedelta(days=999)
            active_upcoming_list = []

        dashboard_data['bookings'][b.id] = {
            'id': b.id,
            'appartment': format_appartment_from_id(b.appartment_id),
            'appartment_id': b.appartment_id,
            'name': b.name,
            'arrival': format_date(b.arrival),
            'departure': format_date(b.departure),
            'stay': (b.departure - b.arrival).days,
            'clearance': (b.arrival - last_occupied).days,
            'portal': b.portal,
            'total': b.total,
            'deposit': b.deposit,
            'phone': b.phone,
            'email': b.email,
            'deposit_made': b.deposit_made,
            'total_made': b.total_made,
            'arrival_in': (b.arrival - today).days,
            'remarks': b.remarks
        }

        current = False
        if b.arrival < today and b.departure >= today:
            current = True
            active_upcoming_list.append({'type':'current', 'id': b.id})
        elif b.arrival >= today and b.arrival <= upcoming:
            if len(active_upcoming_list) == 0:
                active_upcoming_list.append({'type': 'available', 'from': format_date(last_occupied), 'to': format_date(b.arrival)})
                active_upcoming_list.append({'type': 'upcoming', 'id': b.id})
            else:
                active_upcoming_list.append({'type': 'upcoming', 'id': b.id})
        elif b.arrival > upcoming and len(active_upcoming_list) == 0:
            active_upcoming_list.append({'type': 'available', 'from': format_date(last_occupied), 'to': format_date(b.arrival)})
        elif b.arrival > upcoming and active_upcoming_list[-1]['type'] != 'available' and last_occupied < upcoming:
            active_upcoming_list.append({'type': 'available', 'from': format_date(last_occupied), 'to': format_date(b.arrival)})

        last_occupied = b.departure

    dashboard_data['upcoming'][format_appartment_from_id(active_appartment)] = active_upcoming_list

    return dashboard_data

@app.route("/api/dashboard")
@cross_origin(header=["Content-Type", "Authorization"])
@requires_auth
def dashboard():
    response = get_bookings_for_dashboard()
    user_role = 'viewer'
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("permissions"):
            token_scopes = unverified_claims["permissions"]
            if 'role:admin' in token_scopes:
                user_role = 'admin'

    response['role'] = user_role

    return jsonify(response)


@app.route("/api/availability", methods=["GET"])
@cross_origin(header=["Content-Type", "Authorization"])
def availability():
    response = get_availability(request.args.to_dict().get('appartment'))
    return jsonify(response)


@app.route('/api/save', methods=["POST"])
@cross_origin(header=["Content-Type", "Authorization"])
@requires_auth
def save():
    if requires_scope("write:booking"):
        try:
            data = request.get_json()
            booking = Booking.query.filter_by(id=data['id']).first()
            new_booking = False

            if not booking:
                new_booking = True
                booking = Booking(id=data['id'])

            for key, value in data.items():
                if key != 'id':
                    setattr(booking, key, value)

            if new_booking:
                db.session.add(booking)

            db.session.commit()

            response = "success"
            return jsonify(message=response)
        except:
            return jsonify(message="error")
    else:
        return jsonify(message="unauthorized")
        raise AuthError({
            "code": "Unauthorized",
            "description": "You don't have access to this resource"
        }, 403)


@app.route('/api/save-pricing', methods=["POST"])
@cross_origin(header=["Content-Type", "Authorization"])
@requires_auth
def save_pricing():
    if requires_scope("write:pricing"):
        try:
            data = request.get_json()
            for price_class, years in data.items():
                for year, values in years.items():
                    for v, val in enumerate(values):
                        price = Price.query.filter_by(price_class=int(price_class), year=int(year), month=v).first()
                        old_price = price.price
                        if old_price != val:
                            setattr(price, 'price', val)
                            db.session.commit()
            response = "success"
            return jsonify(message=response)
        except:
            return jsonify(message="error")
    else:
        return jsonify(message="unauthorized")
        raise AuthError({
            "code": "Unauthorized",
            "description": "You don't have access to this resource"
        }, 403)

@app.route('/api/base', methods=['GET'])
@cross_origin(header=["Content-Type", "Authorization"])
def base():
    dashboard_data = {
        'prices': get_prices(),
        'price_class_mapping': price_class_mapping
    }
    return jsonify(dashboard_data)

@app.route('/api/calculate', methods=['POST'])
@cross_origin(header=["Content-Type", "Authorization"])
def calculate():
    try:
        data = request.get_json()

        arrival = datetime.strptime(data['arrival'], "%Y-%m-%d").date()
        departure = datetime.strptime(data['departure'], "%Y-%m-%d").date()
        price_class = data['price_class']

        prices = get_prices().get(price_class)
        current_date = arrival
        ccy, ccm = None, None
        summary = {}

        while current_date < departure:
            cy = current_date.year
            cm = current_date.month

            if cy != ccy or cm != ccm:
                week_price = prices.get(cy)[cm-1]
                night_price = week_price / 6
                ccy, ccm = cy, cm

            if str(ccy) not in summary:
                summary[str(ccy)] = {}

            if str(ccm) not in summary[str(ccy)]:
                summary[str(ccy)][str(ccm)] = {
                    'long': datetime.strftime(current_date, "%B").capitalize(),
                    'nights': 1,
                    'ppw': week_price,
                    'ppn': round(night_price, 2),
                    'total': night_price}
            else:
                summary[str(ccy)][str(ccm)]['nights'] += 1
                summary[str(ccy)][str(ccm)]['total'] += night_price

            current_date += timedelta(days=1)

        total_price = 0.0
        total_nights = 0
        for year, months in summary.items():
            for month, info in months.items():
                total_nights += info['nights']
                total_price += round(info['total'], 2)
                info['total'] = round(info['total'], 2)

        summary['total'] = {'total': round(total_price, 2), 'nights': total_nights}

        response = "success"
        return jsonify(summary)
    except:
        return jsonify(message="error")

if __name__ == '__main__':
    app.run(debug=True)
