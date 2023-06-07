# V1

import cv2
import os
import numpy
import time
import requests
import datetime
from PIL import Image
from subprocess import Popen, PIPE
import sys
import pymongo
import threading
import shutil
import argparse

""" Constant Variables """


provider = 'cephProvider'

timeoutSeconds = 30.0
extraTime = 15.0
failDir = '/tmp/staging/uploadFailed'

if not os.path.isdir(failDir):
    os.mkdir(failDir)

parser = argparse.ArgumentParser(description='start uploader')
parser.add_argument('mongoUser', type=str, help='mongodb username')
parser.add_argument('mongoPass', type=str, help='mongodb password')
parser.add_argument('mongoUrl', type=str, help='mongodb URL')
parser.add_argument('rookPrepend', type=str, help='rook prepend')
parser.add_argument('vaultUrl', type=str, help='URL for Vault')

args = parser.parse_args()

prepend = args.rookPrepend
vaultUrl = args.vaultUrl
mongoUser = args.mongoUser
mongoPassword = args.mongoPass
mongoUrl = args.mongoUrl


in_filename = ''
selectedName = ''
path = "/tmp/staging"
logfile = "/tmp/staging/log"
uploadFileName = ''


def up(url, dta, hd, fname, file, logfile):
    r = requests.post(url, data=dta, headers=hd, timeout=3.05)
    print(str(r.status_code)+':' + str(r.content))
    if r.status_code == 200:
        os.remove(file)
        f = open(logfile, "a")
        f.write(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(
            hours=-6))).strftime('%b %d, %Y - %H:%M: ') + 'Success :' + fname + '\n')
        f.close()
    else:
        f = open(logfile, "a")
        f.write(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(
            hours=-6))).strftime('%b %d, %Y - %H:%M: ') + 'Upload Failed :' + fname + '\n')
        f.close


while True:
    with os.scandir(path) as it:
        selectedName = ''
        uploadFileName = ''
        oldestTime = 0
        for entry in it:
            if entry.path == logfile:
                continue
            if entry.is_dir():
                continue
            if oldestTime == 0:
                oldestTime = os.stat(entry.path).st_mtime
                selectedName = entry.path
                uploadFileName = entry.name
            else:
                if os.stat(entry.path).st_mtime - oldestTime < 0:
                    oldestTime = os.stat(entry.path).st_mtime
                    selectedName = entry.path
                    uploadFileName = entry.name

    if selectedName != '':
        client = pymongo.MongoClient(
            "mongodb+srv://"+mongoUser+":"+mongoPassword + mongoUrl)
        db = client.motionDetection
        mongo_vars = db.cameras.find_one(
            {'cameraName': uploadFileName[20:-27]}, {'_id': 0})
        print(uploadFileName[20:-27])
        key = mongo_vars['key']
        secretKey = mongo_vars['secretKey']
        deviceName = mongo_vars['deviceName']
        if len(mongo_vars['deviceName']) > 0:
            print('done loading parameters from mongoDB')
        else:
            print('failed getting parameters from mongoDB')
            continue
        with open(selectedName, 'rb') as payload:
            headers = {'Content-Type': 'application/json',
                       'X-Kerberos-Storage-FileName': uploadFileName,
                       'X-Kerberos-Storage-Capture': 'ab',
                       'X-Kerberos-Storage-Device': deviceName,
                       'X-Kerberos-Storage-AccessKey': key,
                       'X-Kerberos-Storage-SecretAccessKey': secretKey,
                       'X-Kerberos-Storage-Provider': provider,
                       'X-Kerberos-Storage-Directory': prepend
                       }
            try:
                th = threading.Thread(target=up, args=(
                    vaultUrl, payload, headers, uploadFileName, selectedName, logfile))
                th.start()
                th.join(timeoutSeconds + extraTime)
                tryAgain = False
                if th.is_alive():
                    print('upload timed out')
                    f = open(logfile, "a")
                    f.write(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(
                        hours=-6))).strftime('%b %d, %Y - %H:%M: ') + '-------Timeout------- :' + uploadFileName + '\n')
                    f.close()
                    # tryAgain = True
                    if os.path.isfile(selectedName):
                        shutil.copy2(selectedName, failDir +
                                     '/' + uploadFileName)
                        os.remove(selectedName)
                if tryAgain:
                    th = threading.Thread(target=up, args=(
                        vaultUrl, payload, headers, uploadFileName, selectedName, logfile))
                    th.start()
                    th.join(timeoutSeconds + extraTime)
                    if th.is_alive():
                        print('upload timed out')
                        f = open(logfile, "a")
                        f.write(datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-6))).strftime(
                            '%b %d, %Y - %H:%M: ') + '-------Timeout Again, permanent fail for this file------- :' + uploadFileName + '\n')
                        f.close()
                        if os.path.isfile(selectedName):
                            shutil.copy2(selectedName, failDir +
                                         '/' + uploadFileName)
                            os.remove(selectedName)

            except:
                print('shit went to hell')
                if os.path.isfile(selectedName):
                    shutil.copy2(selectedName, failDir + '/' + uploadFileName)
                    os.remove(selectedName)
    else:
        print('\033[2K\r'+'no files to process', end='')
        time.sleep(10)
