import polyline
import gmplot
import pandas as pd
import numpy as np
from flask import render_template, request, redirect, make_response, session, Response
from flask import Flask
from stravalib import Client
from stravalib import unithelper
from StringIO import StringIO
from bs4 import BeautifulSoup

app = Flask(__name__)

app.secret_key = 'DONTCAREWHATTHISIS'

app.question1 = {}
app.question2 = {}
app.question3 = {}

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
      return render_template('welcome.html')
  else:
      return redirect('/main')

@app.route('/main')
def main():
  with open('secrets.txt') as f:
    MY_STRAVA_CLIENT_ID = f.readline().strip()
    MY_STRAVA_CLIENT_SECRET = f.readline().strip()

  with open('maps.txt') as f:
    gid = f.readline().strip()
  session['gid']=gid #google map api key
  
  access_token = getToken(MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET)
  if access_token == None:
      return redirectAuth(MY_STRAVA_CLIENT_ID)
  #session['access_token'] = access_token
  client = Client(access_token=session['access_token'])
  athlete = client.get_athlete() # Get current athlete details
  clubs = athlete.clubs
  session['num_clubs']=len(clubs)
  cnames = []
  cids = []
  for i in range(len(clubs)):
    cnames.append(clubs[i].name)
    cids.append(clubs[i].id)
  session['cids']=cids
  session['cnames']=cnames
  session['athlete_name'] = athlete.firstname + ' ' + athlete.lastname
  return redirect('/cluboptions')

@app.route("/cluboptions", methods=['GET','POST'])
def set_options():
  if request.method == 'GET':
     q = 'Choose a club to analyze.'
     clubs = zip(session['cids'], session['cnames'])
     return render_template('cluboptions.html',question=q,clubs=clubs)
  else:   #request was a POST
     session['cid'] = int(request.form['choice'])
     #also store club name..
     club_dict = dict(zip(session['cids'],session['cnames']))
     session['cname']=club_dict[session['cid']]
     print(club_dict)
  return redirect('/options')

@app.route("/options", methods=['GET','POST'])
def set_options2():
  if request.method == 'GET':
     q = 'What are you interested in seeing?'
     output_types = ['Heatmap of recent club activities',\
                     'Map of recent club activity routes',\
                     'Recent club activities with many achievements',\
                     'Recent club activities with many kudos',\
                     'Recent races run by club members']
     output_inds = range(len(output_types))
     choices = zip(output_inds, output_types)
     return render_template('options.html',question=q,choices=choices)
  else:   #request was a POST
     output_choice = int(request.form['choice2'])
     print output_choice
     if output_choice == 0:
        return redirect('/heatmap')
     if output_choice == 1:
        return redirect('/routemap')
     if output_choice == 2:
        return redirect('/achievements')
     if output_choice == 3:
        return redirect('/kudos')
     if output_choice == 4:
        return redirect('/races')

@app.route("/heatmap")
def heat_map():
  client = Client(access_token=session['access_token'])
  club = get_club_activities(client,session['cid'])
  local_runs = get_local_runs(club)
  data=local_runs
  return make_heat_map(data)  

@app.route("/routemap")
def route_map():
  client = Client(access_token=session['access_token'])
  club = get_club_activities(client,session['cid'])
  local_runs = get_local_runs(club)
  data=local_runs
  return make_route_map(data)  

@app.route("/achievements")
def results_table():
  client = Client(access_token=session['access_token'])
  # get the 5 activities with the most achievements
  club = get_club_activities(client,session['cid'])
  #highest achieving athletes
  subset = club.sort_values('achievement_counts',ascending=False).head(50)
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/activities/'
  urls = [base_url + str(i) for i in subset.ids.tolist()]
  # put in list of lists
  output_list = zip(subset['names'],subset['achievement_counts'], urls)
  return render_template('result.html', table_rows = output_list)

@app.route("/kudos")
def results_table_kudos():
  # get the rivals data frame
  #rivals = nearest_rivals_from_file()
  client = Client(access_token=session['access_token'])
  # get the 5 activities with the most achievements
  club = get_club_activities(client,session['cid'])
  #highest achieving athletes
  subset = club.sort_values('kudos_counts',ascending=False).head(50)
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/activities/'
  urls = [base_url + str(i) for i in subset.ids.tolist()]
  # put in list of lists
  output_list = zip(subset['names'],subset['kudos_counts'], urls)
  return render_template('result_kudos.html', table_rows = output_list)

@app.route("/races")
def races_table():
  client = Client(access_token=session['access_token'])
  # get the 5 activities with the most achievements
  club = get_club_activities(client,session['cid'])
  #races!
  subset = club[club['workout_types']=='1']
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/activities/'
  urls = [base_url + str(i) for i in subset.ids.tolist()]
  # put in list of lists
  output_list = zip(subset['names'],subset['distances'], urls)
  return render_template('races.html', table_rows = output_list)

def get_club_activities(client,cid):
    ids = []
    names = []
    distances = []
    moving_times = []
    total_elevation_gains = []
    start_dates = []
    start_latlngs = []
    start_latitudes = []
    start_longitudes = []
    end_latlngs = []
    maps = []
    average_speeds = []
    achievement_counts = []
    athlete_counts = []
    kudos_counts = []
    workout_types = []
    athletes = []
    firstnames = []
    lastnames = []

    for a in client.get_club_activities(cid,  limit=200):
        ids.append(a.id)
        names.append(a.name)
        distances.append(a.distance)
        moving_times.append(a.moving_time)
        total_elevation_gains.append(a.total_elevation_gain)
        start_dates.append(a.start_date_local)
        start_latlngs.append(a.start_latlng)
        start_latitudes.append(a.start_latitude)
        start_longitudes.append(a.start_longitude)
        end_latlngs.append(a.end_latlng)
        maps.append(a.map)
        average_speeds.append(a.average_speed)
        achievement_counts.append(a.achievement_count)
        athlete_counts.append(a.athlete_count)
        kudos_counts.append(a.kudos_count)
        workout_types.append(a.workout_type)
        firstnames.append(a.athlete.firstname)
        lastnames.append(a.athlete.lastname)

    for i in range(len(start_latitudes)):
        if start_latitudes[i] == None:
            start_latitudes[i] = np.nan
    for i in range(len(start_longitudes)):
        if start_longitudes[i] == None:
            start_longitudes[i] = np.nan

    #convert distances to miles, pull out just the number too
    distances_miles = []
    for d in distances:
        d = unithelper.miles(d).num
        distances_miles.append(d)

    club_dict = {'ids':ids, 'names':names, 'distances':distances_miles, 'moving_times':moving_times,\
                 'total_elevation_gains':total_elevation_gains,'start_dates':start_dates, \
                 'start_latlngs':start_latlngs, 'start_latitudes':start_latitudes,\
                 'start_longitudes':start_longitudes, 'end_latlngs':end_latlngs, 'maps':maps,\
                 'average_speeds':average_speeds, 'achievement_counts':achievement_counts, \
                 'athlete_counts':athlete_counts, 'kudos_counts':kudos_counts, 'workout_types':workout_types,\
                 'firstname':firstnames, 'lastname':lastnames}
    club = pd.DataFrame(data = club_dict)
    return club

#choose threshold :
def define_threshold(data):    
  threshold_degs = [0.5, 1, 2, 5, 10, 20,90]  #how may degrees to define local area box?
  for t in threshold_degs:
    local_runs = data[(data['dlat']<t) & (data['dlon']<t)]
    print('there are ', len(local_runs), ' runs within ',t, '  deg of center')
    if (len(local_runs) > 10):
      break
    else:
      continue
  return t

# Get 'local runs' for plotting maps
def get_local_runs(data):
  #filter for nans
  pd.options.mode.chained_assignment = None # silence warning
  subset = data[(np.isfinite(data['start_latitudes'])) & (np.isfinite(data['start_longitudes']))]
    
  #get median lat, lon to define center
  lat_med = np.median(subset['start_latitudes'])
  lon_med = np.median(subset['start_longitudes'])
  print (lat_med, lon_med)
  session['lat_med'] = lat_med
  session['lon_med'] = lon_med

  # count local runs (+/- 5deg from median)
  subset['dlat'] = subset['start_latitudes'].apply(lambda x: abs(x-lat_med))
  subset['dlon'] = subset['start_longitudes'].apply(lambda x: abs(x-lon_med))

  threshold = define_threshold(subset)
  session['threshold']=threshold
  print('threshold = ',threshold)
  local_runs = subset[(subset['dlat']<threshold) & (subset['dlon']<threshold)]
  return local_runs

def make_heat_map(data):
  threshold = session['threshold']
  ts = [0.5, 1, 2, 5, 10, 20, 90]
  zs = [10, 10, 10, 5, 5, 1] #zoom 1 is all the way out
  zooms = dict(zip(ts, zs)) #zooms dictionary to get a proper zoom for a given threshold
  gmap = gmplot.GoogleMapPlotter(session['lat_med'], session['lon_med'], zooms[threshold])
  heat_lats = []
  heat_lons = []
  for m in data.maps.values:
    summary_lat_lon = polyline.decode(m.summary_polyline)
    lats = [i[0] for i in summary_lat_lon]
    lons = [i[1] for i in summary_lat_lon]
    heat_lats.append(lats)
    heat_lons.append(lons)
  heat_lats = [val for sublist in heat_lats for val in sublist]
  heat_lons = [val for sublist in heat_lons for val in sublist]
  gmap.heatmap(heat_lats,heat_lons)
  output = StringIO()
  gmap.draw_file(output, session['gid'])
  return output.getvalue()

def make_route_map(data):
  threshold = session['threshold']
  ts = [0.5, 1, 2, 5, 10, 20, 90]
  zs = [10, 10, 10, 5, 5, 1] #zoom 1 is all the way out
  zooms = dict(zip(ts, zs)) #zooms dictionary to get a proper zoom for a given threshold
  gmap = gmplot.GoogleMapPlotter(session['lat_med'], session['lon_med'], zooms[threshold])
  for m in data.maps.values:
    summary_lat_lon = polyline.decode(m.summary_polyline)
    lats = [i[0] for i in summary_lat_lon]
    lons = [i[1] for i in summary_lat_lon]
    gmap.plot(lats,lons,'blue', size=100, alpha=0.5, edge_width=5)
  output = StringIO()
  gmap.draw_file(output, session['gid'])
  return output.getvalue()

def redirectAuth(MY_STRAVA_CLIENT_ID):
  client = Client()
  url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID,
                                   redirect_uri=request.url)
  return redirect(url)


def getToken(MY_STRAVA_CLIENT_ID,MY_STRAVA_CLIENT_SECRET ):
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


def test_print(this):
  '''make sure the imports are good'''
  if type(this) == str:
    return this
  else:
    return "hello world"

if __name__ == "__main__":
        app.run(port=33508, debug=True)
