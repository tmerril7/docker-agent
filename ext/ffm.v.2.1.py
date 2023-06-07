import subprocess
import shlex
import argparse
import os
import time
import pymongo
import datetime
import logging
from logging.handlers import RotatingFileHandler

loggerFile = '/var/log/ffmpeg.log'
logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(loggerFile, maxBytes=500000, backupCount=4)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


basepath = '/ramdisk'

parser = argparse.ArgumentParser(
    description='start ffmpeg to record rtsp stream in segments')
parser.add_argument('cameraName', type=str,
                    metavar='CameraName', help='name of camera')
parser.add_argument('mongoUser', type=str, help='mongodb username')
parser.add_argument('mongoPass', type=str, help='mongodb password')
parser.add_argument('mongoUrl', type=str, help='mongodb url')

args = parser.parse_args()


client = pymongo.MongoClient(
    "mongodb+srv://" + args.mongoUser + ":" + args.mongoPass + args.mongoUrl)
db = client.motionDetection

mongoVars = db.cameras.find_one({'cameraName': args.cameraName}, {'_id': 0})

while mongoVars == None:
    logger.info(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-6))).strftime('%b %d, %Y - %H:%M: ')
                + "can't find camera in database")
    time.sleep(10)
    mongoVars = db.cameras.find_one(
        {'cameraName': args.cameraName}, {'_id': 0})
while True:
    try:
        testURL = mongoVars['rtspURL']
        break
    except:
        logger.warning(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-6))).strftime('%b %d, %Y - %H:%M: ')
                       + "no rtspURL in database for this camera")
        time.sleep(10)
        mongoVars = db.cameras.find_one(
            {'cameraName': args.cameraName}, {'_id': 0})


d = shlex.split("ffmpeg -rtsp_transport tcp -stimeout 5000000 -use_wallclock_as_timestamps 1 -i '" +
                mongoVars['rtspURL'] +
                "' -vcodec copy -an -f segment -segment_time 10 -reset_timestamps 1 -strftime 1 '/ramdisk/" +
                args.cameraName +
                "/new_%j-%H.%M.%S.mp4'")


while True:
    time.sleep(1)
    try:
        logger.info('###starting###')

        if not os.path.isdir(basepath + '/' + args.cameraName):
            os.mkdir(basepath + '/' + args.cameraName)
        time.sleep(3)
        with os.scandir(basepath + '/' + args.cameraName) as it:
            count = 0
            for name in it:
                count = count + 1
            if count > 12:
                logger.info('file buffer full - restarting')
                continue
    except:
        logger.warning('problem occurred')
        continue
    sp = subprocess.Popen(d)
    while True:
        try:
            time.sleep(5)
            if sp.returncode != None:
                break
            if sp.poll() != None:
                break
            with os.scandir(basepath + '/' + args.cameraName) as it:
                count = 0
                for name in it:
                    count = count + 1
                if count > 12:
                    sp.terminate()
                    break
        except:
            logger.error('crashed')
            sp.terminate()
            break
    sp.wait()
    if sp.returncode == 0:
        logger.info(sp.returncode)
    if sp.returncode != 0:
        logger.error('it broke')
        logger.info(sp.returncode)
