#!/usr/bin/env python

import gcn
import healpy as hp
import sys
from datetime import datetime
import time
import os
import sys
import getopt
import requests
from astropy.io import fits
import numpy as np
import voeventparse as vp 
import math
import lxml
import app.models
from app.models import db, trigger, realtime_pointing
from app.functions import *

INTEGRAL = [gcn.notice_types.INTEGRAL_SPIACS,
            gcn.notice_types.INTEGRAL_WAKEUP,
            gcn.notice_types.INTEGRAL_WEAK]

FERMI = [gcn.notice_types.FERMI_GBM_FLT_POS,
        gcn.notice_types.FERMI_GBM_GND_POS,
        gcn.notice_types.FERMI_GBM_FIN_POS,
        gcn.notice_types.FERMI_GBM_GND_POS,
        ]

MAXI = [gcn.notice_types.MAXI_UNKNOWN]

CALET = [gcn.notice_types.CALET_GBM_FLT_LC]

HAWC = [171]#gcn.notice_types.HAWC_BURST_MONITOR]

IC = [173, 174]#gcn.notice_types.ICECUBE_ASTROTRACK_GOLD,
        # gcn.notice_types.ICECUBE_ASTROTRACK_BRONZE]

@gcn.handlers.include_notice_types(
    gcn.notice_types.INTEGRAL_SPIACS,
    gcn.notice_types.INTEGRAL_WAKEUP,
    gcn.notice_types.INTEGRAL_WEAK,
    gcn.notice_types.FERMI_GBM_FLT_POS,
    gcn.notice_types.FERMI_GBM_GND_POS,
    gcn.notice_types.FERMI_GBM_FIN_POS,
    gcn.notice_types.FERMI_GBM_GND_POS,
    #gcn.notice_types.MAXI_UNKNOWN,
    gcn.notice_types.CALET_GBM_FLT_LC,
    171, 173, 174,
    # gcn.notice_types.HAWC_BURST_MONITOR,
    # gcn.notice_types.ICECUBE_ASTROTRACK_GOLD,
    # gcn.notice_types.ICECUBE_ASTROTRACK_BRONZE,
    gcn.notice_types.SWIFT_ACTUAL_POINTDIR
    )

def process_gcn(payload, root):

    role = ''

    role = root.attrib['role']
    notice_type = gcn.handlers.get_notice_type(root)

    print("ROLE is ", role)
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}
    

    for key, value in params.items():
        print(key, '=', value)
    keys = params.keys()

    #If a swift_actual_pointdir notice
    if int(params['Packet_Type']) == 103:
        RA = params['Slew_RA']
        Dec = params['Slew_Dec']
        Roll = params['Slew_Roll']
        triggertime = tjdsodtounix(int(params['Slew_TJD']),float(params['Slew_SOD']))
        UTCtrigtime = unixtoutcdt(triggertime)

        pointdir = realtime_pointing(
            timestamp = UTCtrigtime,
            position = "POINT("+str(RA)+" "+str(Dec)+")",
            roll = Roll
        )

        db.session.add(pointdir)
        print("Adding pointing to realtime DB\n")
        db.session.commit()

    #else it has to be a trigger
    elif role != 'test':
        eventtime = root.find('.//ISOTime').text
        IDtime = math.floor(time.mktime(datetime.strptime(eventtime, "%Y-%m-%dT%H:%M:%S.%f").timetuple()))

        try:        
            name = ''
            if notice_type in HAWC:
                trigger_type = "GRB"
                trigger_instrument = "HAWC"
                try:
                    name = 'HAWC ' + params['RUN_NUM'] + params['EVENT_NUM']
                except Exception as E:
                    print(E)
                    name = 'HAWC ' + eventtime
            elif notice_type in IC:
                trigger_type = "neutrino"
                trigger_instrument = "IceCube"
                try:
                    name = 'IceCube ' + params['RUN_NUM'] + params['EVENT_NUM']
                except Exception as E:
                    print(E)
                    name = 'IceCube ' + eventtime
            elif notice_type in INTEGRAL:
                trigger_type = "GRB"
                name = 'INTEGRAL ' + params['TrigID']
                if notice_type == gcn.notice_types.INTEGRAL_SPIACS:
                    trigger_instrument = "INTEGRAL/SPIACS"
                else:
                    trigger_instrument = "INTEGRAL/IBIS"
            elif notice_type in FERMI:
                trigger_type = "GRB"
                name = 'Fermi ' + params['TrigID']
                trigger_instrument = "Fermi/GBM"
            elif notice_type in CALET:
                trigger_type = "GRB"
                name = 'CALET ' + params['TrigID']
                trigger_instrument = "CALET"

        except Exception as E:
            print(E)
        
        has_position = False
        locmapurl = ''
        try:
            v = vp.loads(lxml.etree.tostring(root))
            pos2d=vp.convenience.get_event_position(v)
            ra = pos2d.ra
            dec = pos2d.dec
            pos_error = pos2d.err
            print('ra: %.3f, dec: %.3f, pos_error: %.3f'%(ra,dec,pos_error))
            if 'LocationMap_URL' in params:
                locmapurl=params['LocationMap_URL']
            if np.isclose(ra,0) and np.isclose(dec,0) and np.isclose(pos_error,0):
                # do something
                has_position = False
            elif notice_type in CALET:
                has_position = False
            else:
                has_position = True
        except Exception as E:
            print(E)

        if has_position:
            trig = trigger(
                trigid = IDtime,
                trigger_time = eventtime,
                event_name = [name],
                trigger_type = trigger_type,
                trigger_instruments = [trigger_instrument],
                position = "POINT("+str(ra)+" "+str(dec)+")",
                position_error = pos_error,
                localization_mapurl = locmapurl
            ) 
        else:
            trig = trigger(
                trigid = IDtime,
                trigger_time = eventtime,
                event_name = [name],
                trigger_type = trigger_type,
                trigger_instruments = [trigger_instrument],
                localization_mapurl= locmapurl
            ) 
        #check if already have a DB entry for a trigger at this time
        trigcheck = trigger.query.filter_by(trigid = IDtime).all()
        if len(trigcheck) == 0:
            db.session.add(trig)
            print("Adding trigger to DB\n")
            db.session.commit()
        else:
            if not trigcheck[0].__eq__(trig):
                diffInst=False
                if trigger_instrument not in trigcheck[0].trigger_instruments:
                    trigcheck[0].trigger_instruments.append(trigger_instrument)
                    diffInst=True
                    print('Different instrument')
                if pos_error != trigcheck[0].position_error:
                    if diffInst is True and pos_error < trigcheck[0].position_error:
                        print('Better position, updating')
                        trigcheck[0].position = "POINT("+str(ra)+" "+str(dec)+")"
                        trigcheck[0].position_error= pos_error
                    if diffInst is False:
                        print('New position, updating')
                        trigcheck[0].position = "POINT("+str(ra)+" "+str(dec)+")"
                        trigcheck[0].position_error= pos_error
                if name not in trigcheck[0].event_name:
                    trigcheck[0].event_name.append(name)
                if trigcheck[0].localization_mapurl != locmapurl:
                    trigcheck[0].localization_mapurl=locmapurl

                print("Updating trigger with new info \n")
                db.session.commit()
                
            else:
                print('Identical')

        

def main():
    print('LISTENING')
    gcn.listen(handler=process_gcn)

if len(sys.argv) == 1:    
    main()
else:
    print('parsing local input')
    payload = open(sys.argv[1], 'rb').read()
    root = lxml.etree.fromstring(payload)
    process_gcn(payload, root)