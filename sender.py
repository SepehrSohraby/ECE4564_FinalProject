__author__ = 'Ryan Nour'

import pika
import pika.exceptions
import signal
import sys
import time
import argparse
import json

# Global variable that controls running the app
publish_stats = True

def stop_stats_service(signal=None, frame=None):
    print " Caught exit command"
    publish_stats = False
    sys.exit(0)

# needs to be a read temperature function that reads in data from the TMP006 chip

# needs to be a read QR code function that reads in a person's ticket barcode

# these two items that are acquired from the raspberry pi need to be put into the JSON object created below
try:

    # The message broker host name or IP address
    host = None
    # The virtual host to connect to
    vhost = "/" # Defaults to the root virtual host
    # The credentials to use
    credentials = None
    # The topic to subscribe to
    topic = None

    ### Command Line Argument Parsing ###

    # Creating the argument parser using argparse
    line_parser = argparse.ArgumentParser()

    # Defining the arguments to be expected
    line_parser.add_argument("-b", "--host",
        help="This is the IP address or named address of the message broker to connect to",
        metavar="host", default="localhost", type=str, required=True)
    line_parser.add_argument("-p", "--vhost",
        help="Path to Virtual Host to connect to on the message broker.",
        metavar="vhost", default="/", type=str)
    line_parser.add_argument("-c", "--credentials",
        help="Credentials to use when logging in to message broker",
        metavar="login:password", default="guest:guest", type=str)
    line_parser.add_argument("-k", "--topic",
        help="The routing key for publishing messages to the message broker",
        metavar="routing key", default="group")

    # Parse the arguments
    arguments = line_parser.parse_args()

    # Store Arguments
    host = arguments.host
    vhost = arguments.vhost

    try:
        all_cred = arguments.credentials.split(":")
        credentials = pika.PlainCredentials(all_cred[0], all_cred[1], True)
    except Exception as e:
        print("Error Parsing Credentials")
        raise

    topic = arguments.topic

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
            sample = {"Temperature": None, "QR Code": None}
            sample["Temperature"] = 100.4 #call function that reads in temperature
            sample["QR Code"] = 6545645646 #call function that reads in the QR Code
            # Creating the JSON object to be published
            json_message = json.dumps(sample, indent=1)
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
