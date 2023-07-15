# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect = True)
Base.classes.keys
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(bind=engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes"""
    return(
        f"Available Routes for Hawaii Weather Data:<br/><br>"
        f"Daily Precipitation Totals for Last Year: <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"All Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"Daily Temperature Observations for Station USC00519281 for Last Year: <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"Min, Average & Max Temperatures for Date Range (Specified Start Date formatted as YYYY-MM-DD): <a href=\"/api/v1.0/start_date\">/api/v1.0/start_date<a><br>"
        f"Min, Average & Max Temperatures for Specified Date Range formatted as YYYY-MM-DD/YYYY-MM-DD: <a href=\"/api/v1.0/start_date/end_date\"/api/v1.0/start_date/end_date<a><br>"
        f"NOTE: If no end-date is provided, the trip api calculates stats through 08/23/17<br>" 
    )

# Create a route that queries precipiation levels and dates and returns a dictionary using date as key and precipation as value
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a list of precipitation (prcp)and date (date) data"""
    
       # Query and summarize daily precipitation across all stations for the last year of available data
    
    start_date = '2016-08-22'
    sel = [Measurement.date, 
        func.sum(Measurement.prcp)]
    precipitation = session.query(*sel).\
            filter(Measurement.date >= start_date).\
            group_by(Measurement.date).\
            order_by(Measurement.date).all()
   
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    precipitation_dates = []
    precipitation_totals = []

    for date, dailytotal in precipitation:
        precipitation_dates.append(date)
        precipitation_totals.append(dailytotal)
    
    precipitation_dict = dict(zip(precipitation_dates, precipitation_totals))

    return jsonify(precipitation_dict)

# Create a route that returns a JSON list of stations from the database
@app.route("/api/v1.0/stations")
def station(): 

    """Return a list of all the active Weather stations in Hawaii"""
    # Return a list of active weather stations in Hawaii
    sel = [Measurement.station]
    active_stations = session.query(*sel).\
        group_by(Measurement.station).all()
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    # Convert list of tuples into normal list and return the JSonified list
    list_of_stations = list(np.ravel(active_stations)) 
    return jsonify(list_of_stations)

# Create a route that queries the dates and temp observed for the most active station for the last year of data and returns a JSON list of the temps observed for the last year
@app.route("/api/v1.0/tobs") 
def tobs():
    
    # Query the last 12 months of temperature observation data for the most active station
    start_date = '2016-08-22'
    sel = [Measurement.date, 
        Measurement.tobs]
    station_temps = session.query(*sel).\
            filter(Measurement.date >= start_date, Measurement.station == 'USC00519281').\
            group_by(Measurement.date).\
            order_by(Measurement.date).all()

    session.close()

    # Return a dictionary with the date as key and the daily temperature observation as value
    observation_dates = []
    temperature_observations = []

    for date, observation in station_temps:
        observation_dates.append(date)
        temperature_observations.append(observation)
    
    tobs_dict = dict(zip(observation_dates, temperature_observations))

    return jsonify(tobs_dict)

# Create a route that when given the start date only, returns the minimum, average, and maximum temperature observed for all dates greater than or equal to the start date entered by a user

@app.route("/api/v1.0/<start_date>")
# Define function, set "start" date entered by user as parameter for start_date decorator 
def start_date(start_date, end_date="2017-08-22"):
    # If no end date is provided, the function defaults to 2017-08-23.
    query_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    session.close()

    trip_stats = []
    for min, avg, max in query_result:
        trip_dict = {}
        trip_dict["Min"] = min
        trip_dict["Average"] = avg
        trip_dict["Max"] = max
        trip_stats.append(trip_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if trip_dict['Min']: 
        return jsonify(trip_stats)
    else:
        return jsonify({"error": f"Date {start_date} not found or not formatted as YYYY-MM-DD."}), 404

# Create a route that when given the start date only, returns the minimum, average, and maximum temperature observed for all dates greater than or equal to the start date entered by a user

@app.route("/api/v1.0/<start_date>/<end_date>")
# Define function, set start and end dates entered by user as parameters for start_end_date decorator
def Start_end_date(start_date, end_date):
    # If no valid end date is provided, the function defaults to 2017-08-23.
    query_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    session.close()
    
    trip_stats = []
    for min, avg, max in query_result:
        trip_dict = {}
        trip_dict["Min"] = min
        trip_dict["Average"] = avg
        trip_dict["Max"] = max
        trip_stats.append(trip_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if trip_dict['Min']: 
        return jsonify(trip_stats)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)