__author__ = 'Chris Buehler, Matthew Peak, Ryan Nour, Sepehr Sohraby'

import pika
import pika.exceptions
import signal
import sys
import time
import argparse
import json
import time
import picamera
import RPi.GPIO as GPIO  # new
import subprocess
import Adafruit_TMP.TMP006 as TMP006

# Global variable that controls running the app
publish_stats = True

def stop_stats_service(signal=None, frame=None):
    print " Caught exit command"
    publish_stats = False
    sys.exit(0)
    
def image_save(filename='',i=0):
    i = i+1
    filename = filename + '_' + str(i)
    print filename
    return filename,i

def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0
        
def camera_capture():
    sensor = TMP006.TMP006()
    sensor.begin()
    
    i = 0
    filename = "image_test"
    GPIO.setmode(GPIO.BCM)  # new
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # new
    
    with picamera.PiCamera() as camera:
        camera.start_preview()
        Run = 1
        while Run:
            GPIO.wait_for_edge(18, GPIO.FALLING)  # new
            input_state = GPIO.input(18)
            if input_state == False:
        #    new_filename = image_save(filename, i)
        #    filename2 = new_filename[0]
        #    image = '/home/pi/Desktop/'
        #    camera.capture(image+filename2)
          #if the last reading was low and this one high, print
                camera.capture('/home/pi/Desktop/image4.jpg')
                camera.stop_preview()
                Run = 0
        
    command = "zbarimg"
    location = "/home/pi/Desktop/image4.jpg"
    #result = run_p(command+location)
    result = subprocess.check_output(["zbarimg", location])
    obj_temp = sensor.readObjTempC()
    
    new_result = result.split(":")
    new2_result = new_result[1].split(",")
    
    info_dict = {"Name" : None, "Airliner": None, "Ticket Number": None, "City of Origin": None, "Country of Origin":None,
                    "Temperature": None}
    info_dict["Name"] = new2_result[0]
    info_dict["Airliner"] = new2_result[1]
    info_dict["Ticket Number"] = new2_result[2]
    info_dict["City of Origin"] = new2_result[3]
    info_dict["Country of Origin"] = new2_result[4].rstrip()
    info_dict["Temperature"] = c_to_f(obj_temp)
    
    json_message = json.dumps(info_dict, indent=1)
    print "Sending Message"
    print json_message
    print " "
    
    return json_message

# needs to be a read temperature function that reads in data from the TMP006 chip

# needs to be a read QR code function that reads in a person's ticket barcode

# these two items that are acquired from the raspberry pi need to be put into the JSON object created below
try:

    # The message broker host name or IP address
    host = "netapps.ece.vt.edu"
    # The virtual host to connect to
    vhost = "/2014/fall/tempest" # Defaults to the root virtual host
    # The credentials to use
    credentials2 = "tempest:K1netic;ma7rix29"
    # The topic to subscribe to
    topic = "final_test"
    all_cred = credentials2.split(":")

    credentials = pika.PlainCredentials(all_cred[0],
                             all_cred[1],
                             True)

    # Ensure that the user specified the required arguments
    if host is None:
        print "You must specify a message broker to connect to"
        sys.exit()

    if topic is None:
        print "You must specify a topic to subscribe to"
        sys.exit()

    message_broker = None
    channel = None
    try:
        try:
            msg_broker = pika.BlockingConnection(pika.ConnectionParameters(host=host,virtual_host=vhost,credentials=credentials))
            channel = msg_broker.channel()
        except Exception as e:
            print("Error With Connecting to the Message Broker")
            raise

        ### End of message broker connection ####
        ### Connection to the Exchange  ###
        try:
            channel.exchange_declare(exchange="pi_utilization",type="direct")
        except Exception as e:
            print("Error Declaring the Exchange:\n" + str(e))
            raise
        print "Connected with Exchange"

        # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
        # sent to this app
        # For more info about signals, see: https://scholar.vt.edu/portal/site/0a8757e9-4944-4e33-9007-40096ecada02/page/e9189bdb-af39-4cb4-af04-6d263949f5e2?toolstate-701b9d26-5d9a-4273-9019-dbb635311309=%2FdiscussionForum%2Fmessage%2FdfViewMessageDirect%3FforumId%3D94930%26topicId%3D3507269%26messageId%3D2009512
        signal_num = signal.SIGINT
        try:
            signal.signal(signal_num, stop_stats_service)
            signal_num = signal.SIGTERM
            signal.signal(signal_num, stop_stats_service)
        except ValueError, ve:
            print "Warning: Greceful shutdown may not be possible: Unsupported " \
                  "Signal: " + signal_num

        ### End of Exchange connection ###
        # Loop until the application is asked to quit
        while(publish_stats):
            # Read data from the raspberry pi
            #sample = {"Temperature": None, "QR Code": None}
            #sample["Temperature"] = 100.4 #call function that reads in temperature
            #sample["QR Code"] = 6545645646 #call function that reads in the QR Code
            # Creating the JSON object to be published
            json_message = camera_capture()
            try:
                channel.basic_publish(exchange="pi_utilization", routing_key= topic, body=json_message)
            except Exception as e:
                print "Error while publishing to broker"
                raise
            # Sleep and then loop
            time.sleep(1.0)
        print "Exiting Application"

    except pika.exceptions.AMQPError, ae:
        print "Error: An AMQP Error occured: " + ae.message

    except pika.exceptions.ChannelError, ce:
        print "Error: A channel error occured: " + ce.message

    except Exception, eee:
        print "Error: An unexpected exception occured: " + eee.message

    finally:
        # For closing the channel gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/channel.html#pika.channel.Channel.close
        if channel is not None:
            channel.close()
        # For closing the connection gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/connection.html#pika.connection.Connection.close
        if message_broker is not None:
            message_broker.close()
        sys.exit(0)

except Exception, ee:
    print "Error: " + ee.message
    sys.exit("Error")
