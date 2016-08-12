from flask import Flask, make_response, session
app = Flask(__name__)
import stravalib
@app.route('/')

@app.route("/simple.png")
def simple():
#    import datetime
#    import StringIO
    #get the polyline map using api:
    get_activity_map()
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
#    from matplotlib.dates import DateFormatter
    import polyline
    m = session['map']
    summary_lat_lon = polyline.decode(m.summary_polyline)
    fig=Figure()
    ax=fig.add_subplot(111)
    lats = [i[0] for i in summary_lat_lon]
    lons = [i[1] for i in summary_lat_lon]
#    x=[]
#    y=[]
#    now=datetime.datetime.now()
#    delta=datetime.timedelta(days=1)
#    for i in range(10):
#        x.append(now)
#        now+=delta
#        y.append(random.randint(0, 1000))
#    ax.plot_date(x, y, '-')
#    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax.scatter(lons,lats)
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

def get_activity_map():
# just to see if i can plot my own activity map!
   f = open('secrets.txt', 'r')
   MY_STRAVA_CLIENT_ID = f.readline().strip()
   MY_STRAVA_CLIENT_SECRET = f.readline().strip()
   STORED_ACCESS_TOKEN = f.readline().strip()
   f.close()
   from stravalib import Client
   client = Client(access_token=STORED_ACCESS_TOKEN)
   client.get_athlete(7656735) # Get current athlete details
   #now get most recent activity for this athlete...
   a=client.get_activities(before = "2016-08-11T00:00:00Z",  limit=1)
   session['map']=a.map
   session['name']=a.name   

if __name__ == "__main__":
    app.run(port=33508)
