import app.models
from app.models import db, trigger, realtime_pointing
from app.functions import *

import sys
sys.path.insert(1, './../toolsBat')
from plot_funcs import *
from plotGBM import BAT_tools

BUCKET="bat-targeted"

#Look through the AWS database, check if it doesnt have earthplots for all existing
# trigger. If not existing make it and upload

files_in_bucket = []
for file in list_files(BUCKET):
    name = file['Key'] 
    files_in_bucket.append(name)

triggers =  trigger.query.filter().order_by(trigger.trigid.desc())
print(f"Total: {len(triggers.all())} Added: {len(files_in_bucket)}")

failed = []
for a in triggers:
    trigid = a.trigid
    filename = f"{trigid}_earthplot.png"
    if filename not in files_in_bucket:
        try:
            print("Trigid is: ", trigid)
            trig_selected = trigger.query.filter_by(trigid = trigid).first()
            earthPlot = SwiftEarthPlot(trig_selected.trigger_time, trig_selected.trigid, prompt=False)
            upload_file(earthPlot, BUCKET)
        except:
            print("Failing now")
            failed.append(filename)

print("failed: ", failed) 
