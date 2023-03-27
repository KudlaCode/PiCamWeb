import RPi.GPIO as GPIO
import time

# Set up GPIO pin
pwm_input = 33
input1 = 35
input2 = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_input, GPIO.OUT) # PWM Speed control
GPIO.setup(input1, GPIO.OUT) # Input1
GPIO.setup(input2, GPIO.OUT) # Input2

# move motor forward
def move_forward(seconds):
    GPIO.output(input1, GPIO.HIGH)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.HIGH)
    time.sleep(seconds)
    # GPIO.output(input1, GPIO.LOW)
    # GPIO.output(input2, GPIO.LOW)
    # GPIO.output(pwm_input, GPIO.LOW)

# move motor forward
def move_backward(seconds):
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.HIGH)
    GPIO.output(pwm_input, GPIO.HIGH)
    time.sleep(seconds)
    # GPIO.output(input1, GPIO.LOW)
    # GPIO.output(input2, GPIO.LOW)
    # GPIO.output(pwm_input, GPIO.LOW)

def zero(seconds):
    GPIO.output(input1, GPIO.LOW)
    GPIO.output(input2, GPIO.LOW)
    GPIO.output(pwm_input, GPIO.LOW)
    time.sleep(seconds)

movetime = 5
while True:
    move_forward(movetime)
    zero(2)
    move_backward(movetime)
    zero(2)