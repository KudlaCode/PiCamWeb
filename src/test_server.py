from flask import Flask, render_template, Response, request
import RPi.GPIO as GPIO
import time
#import cv2
import picamera
import io
from threading import Condition

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


# Route to display camera stream
@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
       
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
    print(response)
    return response

@app.route('/move_forward3')
def move_forward_route3():
    secs = 3
    move_forward(input1, input2, secs)
    response = 'Moved forward for ' + str(secs) + ' seconds'
    print(response)
    return response

@app.route('/move_backward')
def move_backward_route():

    move_backward(input1, input2)
    response = 'Moving motor1 backward'
    print(response)
    return response

@app.route('/stop')
def stop_route():
    stop(input1, input2)
    
    response = 'Stopped motor1'
    print(response)
    return response

@app.route('/fire')
def fire():
    print('Firing...')
    secs = 5
    move_backward(input1, input2, 4)
    move_forward(input1, input2, 3)
    response = 'Firing complete'
    print(response)
    return response

@app.route('/motor2_forward')
def motor2_forward():
    
    move_forward(input3, input4, 0.2)
    response = 'Moving motor2 forward'
    print(response)
    return response

@app.route('/motor2_backward')
def motor2_backward():
    
    move_backward(input3, input4)
    response = 'Moving motor2 backward'
    print(response)
    return response

@app.route('/motor2_stop')
def motor2_stop():
    
    stop(input3, input4)
    response = 'Moving motor2 stopped'
    print(response)
    return response

@app.route('/motor2_trigger')
def motor2_trigger():
    
    move_backward(input3, input4, 2)

    move_forward(input3, input4, 1.0)

    response = 'Motor2 trigger called'
    print(response)
    return response

@app.route('/fire_sequence')
def fire_sequence():
    print('starting fire sequence...')
    #turn gun on
    motor2_trigger()
    time.sleep(0.5)
    fire()
    #turn gun off
    motor2_trigger()

    response = 'Full fire sequence completed'
    print(response)
    return response

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