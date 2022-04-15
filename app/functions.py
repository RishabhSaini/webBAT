from datetime import datetime
from astropy.time import Time
import time
from astropy.utils import data
from astropy.io import fits
import numpy as np
from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
import boto3
from botocore.client import Config



def mjdtounix(mjd):
    """Return a floating point UNIX timestamp for a given MJD"""
    return Time(mjd,format='mjd',scale='utc').unix

def tjdsodtounix(tjd,sod):
    '''Convert TJD and SOD pair to unix timestamp'''
    return mjdtounix(tjd+40000)+sod

def tjdsodtodt(tjd,sod):
    '''Convert TJD and SOD pair to datetime'''
    return datetime.fromtimestamp(tjdsodtounix(tjd,sod)) 

def unixtoutcdt(utime):
    '''Return a MySQL format DATETIME string (UTC) for a given unix timestamp'''
    year,month,day,hour,minute,second,null,null,null = time.gmtime(utime)
    return datetime(year,month,day,hour,minute,second)

def unixtime2sc(unixtime):
    """Convert Unix time to Spacecraft time"""
    return int(unixtime) - time.mktime((2001,1,1,0,0,0,0,0,0))+(unixtime-int(unixtime))

def get_latest_ccfile(url):
    url = url.replace(" ","%20")
    req = Request(url)
    a = urlopen(req).read()
    soup = BeautifulSoup(a, 'html.parser')
    x = (soup.find_all('a'))
    urls=[]
    for i in x:
        file_name = i.extract().get_text()
        url_new = url + file_name
        url_new = url_new.replace(" ","%20")
        if url_new[-5:] == ".fits":
          urls.append(url_new)
    urls.sort()
    ccfileurl = urls[-1]
    ccfile = data.download_file(ccfileurl)
    return ccfile

def clock_correction(utime):
    '''Calculate the clock correction'''
    mettime = unixtime2sc(utime)
    # Find the latest CALDB file for clock correction
    clockdirurl = "https://heasarc.gsfc.nasa.gov/FTP/caldb/data/swift/mis/bcf/clock/"
    clockfile = get_latest_ccfile(clockdirurl)

    # Load in the parameters
    hdu = fits.open(clockfile)
    tstart,tstop,toffset,c0,c1,c2,*rest = np.array(hdu[1].data.tolist()).transpose()
    
    #Figure out which parameters to use
    i = np.where(tstart<mettime)[0][-1]
    
    t1 = (mettime-tstart[i])/86400         

    tcorr = toffset[i] + (c0[i] + c1[i]*t1 + c2[i]*t1*t1)*1E-6      
    return tcorr

def unixtime2ccmet(utime):
    ccutime = utime+clock_correction(utime)
    ccmet = unixtime2sc(ccutime)
    return ccmet

def isInt(i):
	try:
		ret = int(i)
		return True
	except:
		return False

def isFloat(i):
	try:
		ret = float(i)
		return True
	except:
		return False


def list_files(bucket):
    """
    Function to list files in a given S3 bucket
    """
    s3 = boto3.client('s3')
    contents = []
    for item in s3.list_objects(Bucket=bucket)['Contents']:
        contents.append(item)

    return contents

def return_image(bucket, key):
    """
    Key: Name of the image (trigid)
    url: direct link to image 
    """
    s3 = boto3.client('s3', config=Config(s3={'addressing_style': 'path'}))
    url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': key}, ExpiresIn = 100)
    return url

def upload_file(file_name, bucket):
    """
    Function to upload a file to an S3 bucket
    """
    object_name = file_name
    s3_client = boto3.client('s3')
    response = s3_client.upload_file(file_name, bucket, object_name)

    return response

def delete_file(file_name, bucket):
    """
    Function to delete a file to an S3 bucket
    """
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=bucket, Key=file_name)
    return 