__author__ = 'Christopher'

import json
import pika
import pika.channel
import pika.exceptions
import signal
import sys
import argparse

# Create a data structure for holding the maximum and minimum values
#passenger_info = { "Name":"", "Destination": "", "Departure": "", "Temperature": 0.0}
passenger_info = {"Name": "", "Airliner": "", "Ticket Number": "", "City of Origin": "", "Country of Origin": "", "Temperature": 0.0}
#print "hello"
class StatsClientChannelHelper:
    """
    This helper class is used to manage a channel and invoke event handlers when
    signals are intercepted
    """

    def __init__(self, channel):
        """
        Create a new StatsClientChannelEvents object

        :param channel: (pika.channel.Channel) The channel object to manage
        :raises ValueError: if channel does not appear to be valid
        :return: None
        """

        if isinstance(channel, pika.channel.Channel):
            self.__channel = channel

        else:
            raise ValueError("No valid channel to manage was passed in")


    def stop_info_client(self, signal=None, frame=None):
        """
        Stops the pika event loop for the managed channel

        :param signal: (int) A number if a intercepted signal caused this handler
                       to be run, otherwise None
        :param frame: A Stack Frame object, if an intercepted signal caused this
                      handler to be run
        :return: None
        """
        # TODO: Attempt to gracefully stop pika's event loop
        # See: https://pika.readthedocs.org/en/0.9.14/modules/adapters/blocking.html#pika.adapters.blocking_connection.BlockingChannel.stop_consuming
        self.__channel.stop_consuming()


def on_new_msg(channel, delivery_info, msg_properties, msg):
    """
    Event handler that processes new messages from the message broker

    For details on interface for this pika event handler, see:
    https://pika.readthedocs.org/en/0.9.14/examples/blocking_consume.html

    :param channel: (pika.Channel) The channel object this message was received
                    from
    :param delivery_info: (pika.spec.Basic.Deliver) Delivery information related
                          to the message just received
    :param msg_properties: (pika.spec.BasicProperties) Additional metadata about
                           the message just received
    :param msg: The message received from the server
    :return: None
    """

    # Parse the JSON message into a dict
    try:
        stats = json.loads(msg)
        #print "test2"
        # Check that the message appears to be well formed

        if "Temperature" not in stats:
            print "Warning: ignoring message: missing 'Temperature' field"

        if "Name" not in stats:
            print "Warning: ignoring message: missing 'Name' field"

        if "City of Origin" not in stats:
            print "Warning: ignoring message: missing 'City of Origin' field"

        if "Airliner" not in stats:
            print "Warning: ignoring message: missing 'Airliner' field"

        else:
            # Message appears well formed

            #
            # Store Name
            #passenger_info["Name"] = stats["Name"]

            # Store Destination
            #passenger_info["Destination"] = stats["Destination"]

            # Store the current value
            passenger_info["Airliner"] = stats["Airliner"]
            passenger_info["Country of Origin"] = stats["Country of Origin"]
            passenger_info["City of Origin"] = stats["City of Origin"]
            passenger_info["Ticket Number"] = stats["Ticket Number"]
            passenger_info["Name"] = stats["Name"]
            # evaluate NET field for max/min status
            passenger_info["Temperature"] = stats["Temperature"]



            print "\nName: %s" %passenger_info["Name"] + "\nAirliner: %s" %passenger_info["Airliner"] + "\nCity of Origin: %s" %passenger_info["City of Origin"] + "\nCountry of Origin: %s" %passenger_info["Country of Origin"]+ "\nTemp: %f" %passenger_info["Temperature"]
            if (passenger_info["Temperature"] >= 100.4):
                print "Warning: Passenger has fever. Please Quarantine."
            if (passenger_info["Temperature"] <= 95):
                    print "Temp: Below expected value. Please retake temperature."

            else:
                print "Passenger is OK."



    except ValueError, ve:
        # Thrown by json.loads() if it could not parse a JSON object
        print "Warning: Discarding Message: received message could not be parsed"



# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:

    # The message broker host name or IP address
    host = "netapps.ece.vt.edu"
    # The virtual host to connect to
    vhost = "/2014/fall/tempest" # Defaults to the root virtual host
    # The credentials to use
    credentials = "tempest:K1netic;ma7rix29"
    # The topic to subscribe to
    topic = "final_test"

    try:
        all_cred = credentials.split(":")

        credentials = pika.PlainCredentials(all_cred[0],
                                 all_cred[1],
                                 True)
    except Exception as e:
        print("Error Parsing Credentials")
        raise
    #topic = arguments.topic

    ### End Command Line Parsing      ###

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
        # TODO: Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided
        msg_broker = pika.BlockingConnection(
            pika.ConnectionParameters(host = host,
                              virtual_host = vhost,
                              credentials = credentials))

        # TODO: Setup the channel and exchange
        channel = msg_broker.channel()
        channel.exchange_declare(exchange="pi_utiization", type="direct")# Setup channel from connected message broker

        print "connected to message broker"

        # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
        # sent to this app
        # For more info about signals, see: https://scholar.vt.edu/portal/site/0a8757e9-4944-4e33-9007-40096ecada02/page/e9189bdb-af39-4cb4-af04-6d263949f5e2?toolstate-701b9d26-5d9a-4273-9019-dbb635311309=%2FdiscussionForum%2Fmessage%2FdfViewMessageDirect%3FforumId%3D94930%26topicId%3D3507269%26messageId%3D2009512
        signal_num = signal.SIGINT
        try:
            # Create a StatsClientChannelEvents object to store a reference to
            # the channel that will need to be shutdown if a signal is caught
            channel_manager = StatsClientChannelHelper(channel)
            signal.signal(signal_num, channel_manager.stop_info_client)
            signal_num = signal.SIGTERM
            signal.signal(signal_num, channel_manager.stop_info_client)

        except ValueError, ve:
            print "Warning: Graceful shutdown may not be possible: Unsupported " \
                  "Signal: " + signal_num

        # TODO: Create a queue
        # --------------------
        # It is up to you to determine what type of queue to create...
        # For example, if you create an exclusive queue, then the queue will
        # only exist as long as your client is connected
        # or you could create a queue that will continue to receive messages
        # even after your client app disconnects.
        #
        # In the short report, you should document what type of queue you create
        # and the series of events that occur at your client and the message broker
        # when your client connects or disconnects. (Slide 10).
        channel = msg_broker.channel()
        my_queue= channel.queue_declare(exclusive=True)

        # TODO: Bind your queue to the message exchange, and register your
        #       new message event handler
        channel.queue_bind(exchange="pi_utilization",
                   queue=my_queue.method.queue,
                   routing_key = topic)



        # TODO: Start pika's event loop
        channel.basic_consume(on_new_msg, queue=my_queue.method.queue, no_ack=True)
        print "Connecting to Server."
        channel.start_consuming()

    except pika.exceptions.AMQPError, ae:
        print "Error: An AMQP Error occured: " + ae.message

    except pika.exceptions.ChannelError, ce:
        print "Error: A channel error occured: " + ce.message

    except Exception, eee:
        print "Error: An unexpected exception occured: " + eee.message

    finally:
        # TODO: Attempt to gracefully shutdown the connection to the message broker
        # For closing the channel gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/channel.html#pika.channel.Channel.close
        if channel is not None:
            channel.close()
        # For closing the connection gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/connection.html#pika.connection.Connection.close
        if message_broker is not None:
            message_broker.close()

except Exception, ee:
    # Add code here to handle the exception, print an error, and exit gracefully
    print "Error: ungraceful connection shutdown"
    print "Please try again"
    sys.exit("Ungraceful Error")
