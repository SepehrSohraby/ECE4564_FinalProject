__author__ = 'Matthew Peak'
import time
import picamera
import RPi.GPIO as GPIO  # new
import subprocess
import Adafruit_TMP.TMP006 as TMP006

def run_p(cmd):
    print("RunP:"+cmd)
    proc=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    result=""
    for line in proc.stdout:
      result=str(line,"utf-8")
    return result
    
def image_save(filename='',i=0):
    i = i+1
    filename = filename + '_' + str(i)
    print filename
    return filename,i

def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0
    
sensor = TMP006.TMP006()
sensor.begin()

i = 0
filename = "image_test"
GPIO.setmode(GPIO.BCM)  # new
GPIO.setup(17, GPIO.IN, GPIO.PUD_UP)  # new

with picamera.PiCamera() as camera:
    camera.start_preview()
    GPIO.wait_for_edge(17, GPIO.FALLING)  # new
#    new_filename = image_save(filename, i)
#    filename2 = new_filename[0]
#    image = '/home/pi/Desktop/'
#    camera.capture(image+filename2)
    camera.capture('/home/pi/Desktop/image4.jpg')
    camera.stop_preview()
    
command = "zbarimg"
location = "/home/pi/Desktop/image3.jpg"
#result = run_p(command+location)
result = subprocess.check_output(["zbarimg", location])
obj_temp = sensor.readObjTempC()

print result
print 'Object temperature: {0:0.3F}*C / {1:0.3F}*F'.format(obj_temp, c_to_f(obj_temp))
