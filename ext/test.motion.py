import av
import av.datasets
import cv2 as cv
import argparse
import imutils
import telegram
import math

learning_rate = 0
maxSpeed = 20
averaging_size = 20
averageVolume = [0]
wholeAverageList = list()
wholeAverage = 0

for i in range(1, averaging_size):
    averageVolume.append(0)
index = 0

resize_height = 400
bw = 40
bh = 20
maxMotion = 0

parser = argparse.ArgumentParser()
parser.add_argument('fileName', type=str, help='input video file name')
parser.add_argument('token', type=str)
parser.add_argument('chat_id', type=str)
args = parser.parse_args()
print(args.fileName)
bot = telegram.Bot(token=args.token)

backSub = cv.createBackgroundSubtractorKNN()

try:
    container = av.open(av.datasets.curated(args.fileName))
except:
    print('Error opening file')

stream = container.streams.video[0]
stream.thread_type = "AUTO"

cXp = 0
cYp = 0

gen = container.decode(stream)
doOnce = True
burnedCount = 0
while True:
    try:
        frame = next(gen)
    except StopIteration:
        break
    while doOnce:
        height = frame.height
        width = frame.width
        # output = cv.VideoWriter('./output.mp4', cv.VideoWriter_fourcc(*'mp4v'),8, (int(resize_height/height*width), resize_height))
        doOnce = False
    while burnedCount < 5:
        resized_frame = cv.resize(frame.to_ndarray(
            format="bgr24"), (int(resize_height/height*width), resize_height))
        fgmask = backSub.apply(resized_frame, learning_rate)
        burnedCount = burnedCount + 1
    resized_frame = cv.resize(frame.to_ndarray(
        format="bgr24"), (int(resize_height/height*width), resize_height))
    fgmask = backSub.apply(resized_frame, learning_rate)
    thresh = cv.threshold(fgmask, 15, 255, cv.THRESH_BINARY)[1]
    thresh = cv.erode(thresh, None, iterations=2)
    thresh = cv.dilate(thresh, None, iterations=4)
    thresh = cv.erode(thresh, None, iterations=2)
    contours = cv.findContours(
        thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    # converted = cv.cvtColor(fgmask, cv.COLOR_GRAY2BGR)
    # print(len(contours))
    max_area = 0.0

    cXd = 0
    cYd = 0
    delta = 0
    for contour in contours:
        perim = cv.arcLength(contour, True)
        approx = cv.approxPolyDP(contour, 0.02 * perim, True)
        resized_frame = cv.drawContours(
            resized_frame, [approx], -1, (0, 255, 255), 2)
        x, y, w, h = cv.boundingRect(approx)
        area = cv.contourArea(approx)
        if area > max_area:
            max_area = area
            brX = x
            brY = y
            brW = w
            brH = h
            M = cv.moments(contour)
    if max_area > 0.0:
        resized_frame = cv.rectangle(
            resized_frame, (brX, brY), (brX+brW, brY+brH), (255, 0, 0), 2)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        cXd = abs(cX - cXp)
        cYd = abs(cY - cYp)
        cXp = cX
        cYp = cY
        delta = int(math.sqrt(cXd * cXd + cYd * cYd))
        if delta < maxSpeed:
            resized_frame = cv.circle(
                resized_frame, (cX, cY), 8, (0, 255, 0), -1)
        else:
            resized_frame = cv.circle(
                resized_frame, (cX, cY), 8, (0, 0, 255), -1)

    if delta < maxSpeed:
        averageVolume[index] = int(max_area)
    else:
        averageVolume[index] = 0
    index += 1

    if index > averaging_size - 1:
        index = 0
    aveMotion = sum(averageVolume)/len(averageVolume)
    if aveMotion > maxMotion:
        maxMotion = aveMotion
        thumbnail = resized_frame.copy()

    wholeAverageList.append(aveMotion)
    wholeAverage = sum(wholeAverageList)/len(wholeAverageList)

    tsize, bline = cv.getTextSize("area: {:.0f}".format(
        max_area), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
    cv.rectangle(resized_frame, (int(resize_height/height*width) -
                 tsize[0], 0, tsize[0], tsize[1]), (255, 255, 255), -1)
    cv.putText(resized_frame, "area: {:.0f}".format(max_area), (int(
        resize_height/height*width)-tsize[0], tsize[1]-int(bline/2)), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    tsize, bline = cv.getTextSize("inst_ave_mot: {:.0f}".format(
        aveMotion), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
    cv.rectangle(resized_frame, (int(resize_height/height*width) -
                 tsize[0], tsize[1], tsize[0], tsize[1]), (255, 255, 255), -1)
    cv.putText(resized_frame, "inst_ave_mot: {:.0f}".format(
        aveMotion), (int(
            resize_height/height*width)-tsize[0], tsize[1]-int(bline/2)+tsize[1]), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    tsize, bline = cv.getTextSize("delta: {:.0f}".format(
        delta), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
    cv.rectangle(resized_frame, (int(resize_height/height*width) -
                 tsize[0], tsize[1]*2, tsize[0], tsize[1]), (255, 255, 255), -1)
    cv.putText(resized_frame, "delta: {:.0f}".format(
        delta), (int(
            resize_height/height*width)-tsize[0], tsize[1]*2-int(bline/2)+tsize[1]), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    tsize, bline = cv.getTextSize("max_inst_ave_mot: {:.0f}".format(
        maxMotion), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
    cv.rectangle(resized_frame, (int(resize_height/height*width) -
                 tsize[0], tsize[1]*3, tsize[0], tsize[1]), (255, 255, 255), -1)
    cv.putText(resized_frame, "max_inst_ave_mot: {:.0f}".format(
        maxMotion), (int(
            resize_height/height*width)-tsize[0], tsize[1]*3-int(bline/2)+tsize[1]), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    tsize, bline = cv.getTextSize("whole_ave: {:.0f}".format(
        wholeAverage), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
    cv.rectangle(resized_frame, (int(resize_height/height*width) -
                 tsize[0], tsize[1]*4, tsize[0], tsize[1]), (255, 255, 255), -1)
    cv.putText(resized_frame, "whole_ave: {:.0f}".format(
        wholeAverage), (int(
            resize_height/height*width)-tsize[0], tsize[1]*4-int(bline/2)+tsize[1]), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

    # output.write(resized_frame)

tsize, bline = cv.getTextSize("whole_ave: {:.0f}".format(
    wholeAverage), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
cv.rectangle(thumbnail, (int(resize_height/height*width) -
                         tsize[0], 0, tsize[0], tsize[1]), (255, 255, 255), -1)
cv.putText(thumbnail, "whole_ave: {:.0f}".format(wholeAverage), (int(
    resize_height/height*width)-tsize[0], tsize[1]-int(bline/2)), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
tsize, bline = cv.getTextSize("max_inst_ave_mot: {:.0f}".format(
    maxMotion), cv.FONT_HERSHEY_SIMPLEX, .7, 2)
cv.rectangle(thumbnail, (int(resize_height/height*width) -
                         tsize[0], tsize[1], tsize[0], tsize[1]), (255, 255, 255), -1)
cv.putText(thumbnail, "max_inst_ave_mot: {:.0f}".format(
    maxMotion), (int(
        resize_height/height*width)-tsize[0], tsize[1]-int(bline/2)+tsize[1]), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
cv.imwrite('/tmp/thumbnail.png', thumbnail)
container.close()
# output.release()
bot.send_photo(chat_id=args.chat_id, photo=open('/tmp/thumbnail.png', 'rb'))

# x,y,w,h = cv.boundingRect(cnt)
# cv.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
