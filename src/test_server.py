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
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_input, GPIO.OUT) # PWM Speed control
GPIO.setup(input1, GPIO.OUT) # Input1
GPIO.setup(input2, GPIO.OUT) # Input2
global move_duration
move_duration = 5

# Initialize camera
#camera = cv2.VideoCapture(0)
#camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Route to display camera stream
@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
       
        #success, frame = camera.read()
        #if not success:
        #    break
        #ret, jpeg = cv2.imencode('.jpg', frame)
        #frame = jpeg.tobytes()
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
    secs = move_duration
    move_forward(secs)
    response = 'Moved forward for ' + str(secs) + ' seconds'
    print(response)
    return response

@app.route('/move_forward3')
def move_forward_route3():
    secs = 3
    move_forward(secs)
    response = 'Moved forward for ' + str(secs) + ' seconds'
    print(response)
    return response

@app.route('/move_backward')
def move_backward_route():
    secs = move_duration
    move_backward(secs)
    response = 'Moved backward for ' + str(secs) + ' seconds'
    print(response)
    return response

@app.route('/stop')
def stop_route():
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.LOW)
    
    response = 'Stopped'
    print(response)
    return response

@app.route('/fire')
def fire():
    print('Firing...')
    secs = 5
    move_backward(4)
    move_forward(3)
    response = 'Firing complete'
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