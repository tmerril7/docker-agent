import av
import av.datasets
import cv2 as cv
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('fileName', type=str, help='input video file name')

args = parser.parse_args()

backSub = cv.createBackgroundSubtractorMOG2()

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
        output = cv.VideoWriter(
            '/tmp/output.mp4', cv.VideoWriter_fourcc(*'MP4V'), 10, (width, height))
        print(frame.to_ndarray(format="bgr24"))
        doOnce = False
    output.write(frame.to_ndarray(format="bgr24"))

container.close()
output.release()
