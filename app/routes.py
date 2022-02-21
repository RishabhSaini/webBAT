import imp
from flask import Flask, request, jsonify, render_template, redirect, flash, url_for, abort
from app import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from .models import trigger, realtime_pointing, db
from app import forms
from app import functions

import sys
sys.path.insert(1, './../toolsBat')
from plotGBM import BAT_tools

import time
from datetime import datetime
import math

BUCKET="bat-targeted"

@app.route('/')
@app.route('/index')
def index():
	triggers = trigger.query.filter().order_by(trigger.trigid.desc())
	return render_template("index.html", triggers=triggers)

@app.route('/trigger_report', methods=['POST', 'GET'])
def trigger_report():
	trigid = request.args.get('trigid')
	url = functions.return_image(BUCKET, f'EarthPlot.png')
	print("Url is", url)
	try:
		#this is an incredibly shitty way to do this. fix later
		trigres = db.session.query(trigger, func.ST_AsText(trigger.position).label('position')).filter_by(trigid=trigid).all()[0]
		trigobj = trigres[0]
		trigobj.position = trigres[1]
		#time_trig = trigobj.trigger_time
		#print("Time is:",time_trig)

		#
		#Upload file return direct link. Same base but different name of file (based on trigid)
		#Task go through the databse and produce images from trigids for which it doesnt already exist.
		#Then create and upload on database. 
		#Clicking th etirgger report should load the file from the database
		#Function: 

	except Exception as E:
		print(E)
		abort(404)
	
	#if trigobj.swift_radec is None:
	realtimepoint = db.session.query(
		realtime_pointing.timestamp, 
		func.ST_AsText(realtime_pointing.position).label('position'),
		realtime_pointing.roll).filter(
			realtime_pointing.timestamp<trigobj.trigger_time
		).order_by(realtime_pointing.timestamp.desc()).first()
		#url = url return 
	return render_template("trigger_report.html",trigobj = trigobj, realtimepoint=realtimepoint, url=url)


@app.route('/realtime_point')
def realtime_point():
	points = db.session.query(
		realtime_pointing.timestamp,
		func.ST_AsText(realtime_pointing.position).label('position'),
		realtime_pointing.roll).order_by(realtime_pointing.timestamp.desc())
	return render_template("realtime_point.html", points=points)

@app.route('/submit_trigger', methods=['POST','GET'])
def new_trigger():
	form = forms.SubmitTriggerForm()

	if request.method == 'POST':
		#initialize trigger object
		trig = trigger()
		trig.event_name = form.event_name.data
		trig.trigger_instruments = [form.trigger_instrument.data]
		trig.trigger_type = form.trigger_type.data
		trig.trigger_time = form.trigtime.data
		print(trig.trigger_time)

		if trig.event_name == 'None' or trig.trigger_instruments == ['None'] or trig.trigger_type == 'None' or trig.trigger_time == 'None':
			flash("Name, Instrument, Type and Time are all required values")
			return render_template("new_trigger_form.html", form = form)

		if (form.ra.data != None) and (not functions.isFloat(form.ra.data) or not functions.isFloat(form.dec.data)):
			flash("RA, Dec, and Error must be decimal")
			return render_template('new_trigger_form.html', form=form)

		if form.ra.data != 'None' and form.dec.data != 'None':
			trig.position="POINT("+str(form.ra.data)+" "+str(form.dec.data)+")"
			trig.position_error = form.error.data

		IDtime = math.floor(time.mktime(trig.trigger_time.timetuple()))
		trigcheck = trigger.query.filter_by(trigid = IDtime).all()
		if len(trigcheck) != 0:
			flash("Trigger already exists, the report can be found here {triglink}.")
			return render_template('new_trigger_form.html', form=form)
		db.session.add(trig)
		db.session.commit()



	return render_template("new_trigger_form.html", form=form)

@app.errorhandler(404)
def page_not_found(error):
	return render_template('404.html'), 404