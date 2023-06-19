import av
import av.datasets
import cv2 as cv
import argparse

resize_height = 400

parser = argparse.ArgumentParser()

parser.add_argument('fileName', type=str, help='input video file name')

args = parser.parse_args()

backSub = cv.createBackgroundSubtractorKNN()

try:
    container = av.open(av.datasets.curated(args.fileName))
except:
    print('Error opening file')

stream = container.streams.video[0]
stream.thread_type = "AUTO"


gen = container.decode(stream)
doOnce = True
while True:
    try:
        frame = next(gen)
    except StopIteration:
        break
    while doOnce:
        height = frame.height
        width = frame.width
        output = cv.VideoWriter('./output.mp4', cv.VideoWriter_fourcc(*'mp4v'), 20, (int(resize_height/height*width), resize_height),False)
        doOnce = False
    resized_frame = cv.resize(frame.to_ndarray(format="bgr24"), (int(resize_height/height*width), resize_height))
    fgmask = backSub.apply(resized_frame)
    contours, hierarchy = cv.findContours(fgmask,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
    frame_w_contours = cv.drawContours(fgmask,contours,-1,(255,0,0),1)

    #cv.imshow('frame',frame_w_contours)
    output.write(frame_w_contours)

container.close()
output.release()
