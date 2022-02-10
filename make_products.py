import app.models
from app.models import db, trigger, realtime_pointing
from app.functions import *

import sys
sys.path.insert(1, './../toolsBat')
from plot_funcs import *
from plotGBM import BAT_tools

from imgExport import export_images

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

BUCKET="bat-targeted"

#time_trig = trigobj.trigger_time
#p = BAT_tools() 
#p.justPlot(time_trig)

##Plotfuncs.py move to toolsBat : Done
##Call to produce EarthMap (battools.py) and Skymap(plotgbm.py) from toolsBat
##Upload to S3 buckets and file name standard trigid_(earthmap/skymap)

#Dont mix both 


##for loop 
trigid = 1642548038
trig_selected = trigger.query.filter_by(trigid = trigid).first()

filenameipynb = f'./../toolsBat/{trigid}_skymap.ipynb'
filename = f'../toolsBat/{trigid}_skymap.png'

notebook_filename = './../toolsBat/Triak.ipynb'
with open(notebook_filename) as f:
    nb = nbformat.read(f, as_version=4)
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
ep.preprocess(nb, {'metadata': {'path': './../toolsBat/'}})
with open(filenameipynb, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

#export_images(filenameipynb, filename, "/images")

earthPlot = SwiftEarthPlot(trig_selected.trigger_time, trig_selected.trigid)
#skyMap = BAT_tools().justPlot(trig_selected.trigger_time, trig_selected.trigid)
upload_file(filename, BUCKET)