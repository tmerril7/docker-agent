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
burning = True
burnedCount = 0
while True:
    try:
        frame = next(gen)
    except StopIteration:
        break
    while doOnce:
        height = frame.height
        width = frame.width
        output = cv.VideoWriter('./output.mp4', cv.VideoWriter_fourcc(*'mp4v'),
                                20, (int(resize_height/height*width), resize_height))
        doOnce = False
    while burnedCount < 5:
        resized_frame = cv.resize(frame.to_ndarray(
            format="bgr24"), (int(resize_height/height*width), resize_height))
        fgmask = backSub.apply(resized_frame)
        burnedCount = burnedCount + 1
    resized_frame = cv.resize(frame.to_ndarray(
        format="bgr24"), (int(resize_height/height*width), resize_height))
    fgmask = backSub.apply(resized_frame)
    thresh = cv.threshold(fgmask, 15, 255, cv.THRESH_BINARY)[1]
    thresh = cv.erode(thresh, None, iterations=2)
    thresh = cv.dilate(thresh, None, iterations=2)
    contours, hierarchy = cv.findContours(
        thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    converted = cv.cvtColor(fgmask, cv.COLOR_GRAY2BGR)
    frame_w_contours = cv.drawContours(
        converted, contours, -1, (0, 0, 255), -1)

    # cv.imshow('frame',frame_w_contours)
    output.write(frame_w_contours)

container.close()
output.release()
