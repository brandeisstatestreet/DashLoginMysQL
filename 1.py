import mysql.connector
from werkzeug.wsgi import DispatcherMiddleware
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import dash
import dash_core_components as dcc
import dash_html_components as html
from pandas_datareader.data import DataReader
import time
from collections import deque
import plotly.graph_objs as go
import random
from dash.dependencies import Output, Input
from werkzeug.serving import run_simple

#mydb = mysql.connector.connect(
  #host="localhost",
  #user="root",
  #passwd="YourOwn",
  #database="statestreet"
#)

#mycursor = mydb.cursor()

#mycursor.execute("CREATE TABLE accounts (id int(11) NOT NULL AUTO_INCREMENT, username varchar(50) NOT NULL, password varchar(255) NOT NULL,email varchar(100) NOT NULL, PRIMARY KEY (`id`))")

#a = "INSERT INTO accounts (id, username, password, email) VALUES (%s, %s, %s, %s)"
#b = ("1", "dudu", "dudu123", "dudu@test.com")
#mycursor.execute(a,b)
#mydb.commit()

app = Flask(__name__)


dpp = dash.Dash('vehicle-data',server = app, url_base_pathname='/dashboard/')

max_length = 50
times = deque(maxlen=max_length)
oil_temps = deque(maxlen=max_length)
intake_temps = deque(maxlen=max_length)
coolant_temps = deque(maxlen=max_length)
rpms = deque(maxlen=max_length)
speeds = deque(maxlen=max_length)
throttle_pos = deque(maxlen=max_length)

data_dict = {"Oil Temperature":oil_temps,
"Intake Temperature": intake_temps,
"Coolant Temperature": coolant_temps,
"RPM":rpms,
"Speed":speeds,
"Throttle Position":throttle_pos}




def update_obd_values(times, oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos):

    times.append(time.time())
    if len(times) == 1:
        #starting relevant values
        oil_temps.append(random.randrange(180,230))
        intake_temps.append(random.randrange(95,115))
        coolant_temps.append(random.randrange(170,220))
        rpms.append(random.randrange(1000,9500))
        speeds.append(random.randrange(30,140))
        throttle_pos.append(random.randrange(10,90))
    else:
        for data_of_interest in [oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos]:
            data_of_interest.append(data_of_interest[-1]+data_of_interest[-1]*random.uniform(-0.0001,0.0001))

    return times, oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos

times, oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos = update_obd_values(times, oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos)

dpp.layout = html.Div([
    html.Div([
        html.H2('Vehicle Data',
                style={'float': 'left',
                       }),
        ]),
    dcc.Dropdown(id='vehicle-data-name',
                 options=[{'label': s, 'value': s}
                          for s in data_dict.keys()],
                 value=['Coolant Temperature','Oil Temperature','Intake Temperature'],
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs'), className='row'),
    dcc.Interval(
        id='graph-update',
        interval=100,
        n_intervals=0),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})


@dpp.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('vehicle-data-name', 'value'), dash.dependencies.Input('graph-update', 'n_intervals')])

def update_graph(data_names,n):
    graphs = []
    update_obd_values(times, oil_temps, intake_temps, coolant_temps, rpms, speeds, throttle_pos)
    if len(data_names)>2:
        class_choice = 'col s12 m6 l4'
    elif len(data_names) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'


    for data_name in data_names:

        data = go.Scatter(
            x=list(times),
            y=list(data_dict[data_name]),
            name='Scatter',
            fill="tozeroy",
            fillcolor="#6897bb"
            )

        graphs.append(html.Div(dcc.Graph(
            id=data_name,
            animate=True,
            figure={'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(times),max(times)]),
                                                        yaxis=dict(range=[min(data_dict[data_name]),max(data_dict[data_name])]),
                                                        margin={'l':50,'r':1,'t':45,'b':1},
                                                        title='{}'.format(data_name))}
            ), className=class_choice))

    return graphs



external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    dpp.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    dpp.scripts.append_script({'external_url': js})


# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Wcssm1229,'
app.config['MYSQL_DB'] = 'statestreet'

# Intialize MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('render_dashboard'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


@app.route('/dashboard/')
def render_dashboard():
    return redirect('/dash1')


app = DispatcherMiddleware(app, {
    '/dash1': dpp.server
})

if __name__ == '__main__':
    run_simple('0.0.0.0', 8080, app, use_reloader=True, use_debugger=True)