from flask import Flask, render_template, Response, request, jsonify
import RPi.GPIO as GPIO
import time
import cv2
#from cv2 import cv
import picamera
from picamera.array import PiRGBArray
import io
from threading import Condition
import random
import numpy as np

#This is to pull the information about what each object is called
classNames = []
classFile = "./../files/coco.names"
with open(classFile,"rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

#This is to pull the information about what each object should look like
configPath = "./../files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "./../files/frozen_inference_graph.pb"

#This is some set up values to get good results
net = cv2.dnn_DetectionModel(weightsPath,configPath)
net.setInputSize(320,320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

#This is to set up what the drawn box size/colour is and the font/size/colour of the name tag and confidence label   
def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img,confThreshold=thres,nmsThreshold=nms)
#Below has been commented out, if you want to print each sighting of an object to the console you can uncomment below     
#print(classIds,bbox)
    if len(objects) == 0: objects = classNames
    objectInfo =[]
    if len(classIds) != 0:
        for classId, confidence,box in zip(classIds.flatten(),confs.flatten(),bbox):
            className = classNames[classId - 1]
            if className in objects: 
                objectInfo.append([className, confidence])
                if (draw):
                    cv2.rectangle(img,box,color=(0,255,0),thickness=2)
                    cv2.putText(img,classNames[classId-1].upper(), (box[0]+10,box[1]+30), 
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
                    cv2.putText(img,str(round(confidence*100,2)), (box[0]+200,box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
    
    return img,objectInfo


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

app = Flask(__name__)

# Set up GPIO pin
pwm_input = 33
input1 = 35
input2 = 37
input3 = 31
input4 = 33
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_input, GPIO.OUT) # PWM Speed control
GPIO.setup(input1, GPIO.OUT) # Input1
GPIO.setup(input2, GPIO.OUT) # Input2
GPIO.setup(input3, GPIO.OUT) # Input1
GPIO.setup(input4, GPIO.OUT) # Input2
global move_duration
move_duration = 5
logging_text = ''

def log(line):
    print(line)
    global logging_text
    logging_text += line + "\n"

# Route to display camera stream
@app.route('/')
def index():
    return render_template('index.html')

# Route to stream video
@app.route('/video_feed')
def video_feed():
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_move_duration', methods=['POST'])
def set_move_duration():
    # Get the value from the text field
    #value = int(request.form['value'])
    formValue = request.form.get('value') 
    #formValue = request.form['value']
    value = None
    try:
        value = int(formValue)
    except:
        print("Error converting to int")

    if type(value) == int:
        move_duration = value
        print('Move duration set to ' + str(move_duration))
    else:
        print('Invalid value for move duration ' + str(request.form['value']))
        print('Value was ' + str(value))
        print('Value type was ' + str(type(value)))
    

    return render_template('index.html')



# Route to control GPIO pin
@app.route('/gpio')
def gpio():
    GPIO.output(11, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(11, GPIO.LOW)
    return 'GPIO Pin Set'

@app.route('/move_forward')
def move_forward_route():
    move_forward(input1, input2)
    response = 'Moving motor1 forward'
    log(response)
    return response

@app.route('/move_forward3')
def move_forward_route3():
    secs = 3
    move_forward(input1, input2, secs)
    response = 'Moved forward for ' + str(secs) + ' seconds'
    log(response)
    return response

@app.route('/move_backward')
def move_backward_route():

    move_backward(input1, input2)
    response = 'Moving motor1 backward'
    log(response)
    return response

@app.route('/stop')
def stop_route():
    stop(input1, input2)
    
    response = 'Stopped motor1'
    log(response)
    return response

@app.route('/fire')
def fire():
    log('Firing...')
    secs = 5
    move_backward(input1, input2, 4)
    move_forward(input1, input2, 3)
    response = 'Firing complete'
    log(response)
    return response

@app.route('/motor2_forward')
def motor2_forward():
    
    move_forward(input3, input4, 0.2)
    response = 'Moving motor2 forward'
    log(response)
    return response

@app.route('/motor2_backward')
def motor2_backward():
    
    move_backward(input3, input4)
    response = 'Moving motor2 backward'
    log(response)
    return response

@app.route('/motor2_stop')
def motor2_stop():
    
    stop(input3, input4)
    response = 'Moving motor2 stopped'
    log(response)
    return response

@app.route('/motor2_trigger')
def motor2_trigger():
    
    move_backward(input3, input4, 2)

    move_forward(input3, input4, 1.0)

    response = 'Motor2 trigger called'
    log(response)
    return response

@app.route('/fire_sequence')
def fire_sequence():
    log('starting fire sequence...')
    #turn gun on
    motor2_trigger()
    time.sleep(0.5)
    fire()
    #turn gun off
    motor2_trigger()

    response = 'Full fire sequence completed'
    log(response)
    return response

# Define a route for the AJAX call
@app.route('/get_data')
def get_data():
    # Generate new data
    global logging_text
    data = logging_text

    # Return data in JSON format
    return jsonify({'data': data})

# move motor forward
def move_forward():
    GPIO.output(input1, GPIO.HIGH)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.HIGH)

def move_forward(seconds):
    GPIO.output(input1, GPIO.HIGH)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.LOW)


def move_forward(firstInput, secondInput, seconds = -1):
    GPIO.output(firstInput, GPIO.HIGH)
    GPIO.output(secondInput, GPIO.LOW)
    if seconds > 0:
        time.sleep(seconds)
        stop(firstInput, secondInput)



def stop(firstInput, secondInput):
    GPIO.output(firstInput, GPIO.LOW)
    GPIO.output(secondInput, GPIO.LOW)

# move motor forward
def move_backward():
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.HIGH)
    GPIO.output(pwm_input, GPIO.HIGH)

def move_backward(seconds):
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.HIGH)
    GPIO.output(pwm_input, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.LOW)

def move_backward(firstInput, secondInput, seconds = -1):
    GPIO.output(firstInput, GPIO.LOW)
    GPIO.output(secondInput, GPIO.HIGH)
    if seconds > 0:
        time.sleep(seconds)
        stop(firstInput, secondInput)

def gen(camera):
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame

            #image analysis
            inp = np.asarray(bytearray(frame), dtype=np.uint8)
            cv_image = cv2.imdecode(inp,cv2.IMREAD_COLOR)
            result, objectInfo = getObjects(cv_image,0.45,0.2, objects=['person'])
            if len(objectInfo) != 0:
                confidence = objectInfo[0][1]
                log('Person detected')
                log('Confidence: ' + str( confidence ))
                if confidence >= 0.65:
                    fire_sequence()



            cv2.imwrite('t.jpg', result)
       
        #yield (b'--frame\r\n'
        #       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('t.jpg', 'rb').read() + b'\r\n')

if __name__ == '__main__':
    with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
        output = StreamingOutput()
        #Uncomment the next line to change your Pi's Camera rotation (in degrees)
        #camera.rotation = 90
        camera.start_recording(output, format='mjpeg')

        try:
            app.run(host='192.168.2.119', port=8000, debug=False)
        except Exception as e:
            print("Error: " + str(e))
        finally:
            camera.stop_recording()
            camera.close()
            GPIO.cleanup()
            print("shutdown...")