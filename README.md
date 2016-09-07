Strava Developer Challenge

See directory strava-club-highlights-gcloud for the submitted app.

See app\_gcloud for a very simple app.

See ipynb for scratch work used to develop apps.



A simple flask app using the Strava API. 

Strava Club Highlights -- highlights recent activities from your clubs

A user selects one of their Strava clubs, then the app allows to user to view::

1) A heatmap of your club's recent activity locations

2) A map of your club's recent routes

3) A sorted list of high-achieving activities

4) A sorted list of high-kudo activities

5) A list of races run by club members recently


Currently deployed at http://strava-club-highlights.appspot.com/

To run locally, enter a virtual environment with 

>virtualenv env

Or, if that doesn't work:

>virtualenv -p python2.7 env

Then:

>source env/bin/activate

>pip install -r requirements.txt

and

>python main.py 

A flask app should be running at http://127.0.0.1:33508 

