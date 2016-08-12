from flask import Flask, make_response, session, request, render_template, redirect
#import all the things we need
import StringIO
import stravalib
from stravalib import Client
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import polyline

app = Flask(__name__)

app.secret_key = 'DONTCAREWHATTHISIS'

app.question1={}
app.question1['What is your favorite song or artist?']=('Song','Artist')

app.nquestion1=len(app.question1)

#get the secrets, they should be one directory up from here
f = open('../secrets.txt', 'r')
MY_STRAVA_CLIENT_ID = f.readline().strip()
MY_STRAVA_CLIENT_SECRET = f.readline().strip()
f.close()

@app.route('/')
@app.route('/index',methods=['GET', 'POST'])
def index():
    nquestion1=app.nquestion1
    if request.method == 'GET':
        return render_template('welcome.html',num=nquestion1)
    else:
        return redirect('/main')
 
@app.route('/main')
def main():
    access_token = getToken()
    if access_token == None:
        return redirectAuth()
    client = Client(access_token=access_token)
    athlete = client.get_athlete() # Get current athlete details
    #if you want a simple output of first name, last name, just use this line:
    #return athlete.firstname + ' ' + athlete.lastname
    #now get most recent activity for this athlete...
    names = []
    maps = []
    for a in client.get_activities(before = "2016-08-12T00:00:00Z",  limit=1):
        names.append(a.name)
        maps.append(a.map)
    # another simple output for this bit is to return the name of the route
    #return names[0]

    # but a sightly more complicated output is this matplotlib figure --
    m = maps[0]
    summary_lat_lon = polyline.decode(m.summary_polyline)
    lats = [i[0] for i in summary_lat_lon]
    lons = [i[1] for i in summary_lat_lon]
    session['name']=names[0]
    session['lats']=lats
    session['lons']=lons
    return redirect('/simple.png')


@app.route("/simple.png")
def simple():
    #get the polyline map using api:
    lons=session['lons']
    lats=session['lats']
    name=session['name']
    fig=Figure()
    ax=fig.add_subplot(111)
    ax.scatter(lons,lats)
    ax.set_title('map for your activity: ' + name)
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


def redirectAuth():
    client = Client()
    url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID,
                                   redirect_uri=request.url)
    return redirect(url)


def getToken():
    access_token = session.get('access_token')
    if access_token != None:
        return access_token
    # the code is in the results thingy!
    code = request.args.get('code')
    if code == None:
        return None
    client = Client()
    access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID,\
                                                  client_secret=MY_STRAVA_CLIENT_SECRET,\
                                                  code=code)
    session['access_token'] = access_token
    return access_token


if __name__ == "__main__":
    app.run(port=33508, debug=True)
