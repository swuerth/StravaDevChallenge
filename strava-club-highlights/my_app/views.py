import polyline
import gmplot
import pandas as pd
import numpy as np
#import subprocess #for printing stdout to app
#import time
from flask import render_template, request, redirect, make_response, session, Response
from my_app import app, auth
from stravalib import Client
from stravalib import unithelper
from StringIO import StringIO

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

  access_token = auth.getToken(MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET)
  if access_token == None:
      return auth.redirectAuth(MY_STRAVA_CLIENT_ID)
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
  return redirect('/options')

@app.route("/options", methods=['GET','POST'])
def set_options():
  if request.method == 'GET':
     q = 'Choose a club to analyze.'
     clubs = zip(session['cids'], session['cnames'])
     return render_template('options.html',question=q,clubs=clubs)
#ans1=cn1,ans2=cn2,ans3=cn3,\
 #                           id1=id1,id2=id2,id3=id3)
  else:   #request was a POST
     session['cid'] = int(request.form['choice'])
     #also store club name..
     club_dict = dict(zip(session['cids'],session['cnames']))
     session['cname']=club_dict[session['cid']]
     print(club_dict)
  return redirect('/result2')

@app.route("/result2")
def heat_map():
  client = Client(access_token=session['access_token'])
  club = get_club_activities(client,session['cid'])
  local_runs = get_local_runs(club)
  data=local_runs
  return make_heat_map(data)  

@app.route("/result")
def results_table():

  # get the rivals data frame
  #rivals = nearest_rivals_from_file()
  client = Client(access_token=session['access_token'])
  # get the 5 activities with the most achievements
  club = get_club_activities(client,session['cid'])
  #highest achieving athletes
  subset = club.sort_values('achievement_counts',ascending=False).head(10)
  #here, route progress to screen...
  #rivals = nearest_rivals(client, max_rivals = 10)
  #rivals = nearest_rivals_from_file()
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/activities/'
  urls = [base_url + str(i) for i in subset.ids.tolist()]
  # put in list of lists
  output_list = zip(subset['names'],subset['achievement_counts'], urls)
  #rivals_list = zip(rivals['athlete_name'], rivals['counts'], urls)
  return render_template('result.html', table_rows = output_list)

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
#  response = make_response(output.getvalue())
  gmap.draw_file(output)
  return output.getvalue()

