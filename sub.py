#!/usr/bin/python

# Copyright (c) 2010-2013 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution. 
#
# The Eclipse Distribution License is available at 
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial implementation
# Copyright (c) 2010,2011 Roger Light <roger@atchoo.org>
# All rights reserved.

# This shows a simple example of an MQTT subscriber.

import sys
import socket
import fcntl
import struct
import subprocess
import os
import datetime
import re
import logging
try:
    import paho.mqtt.client as mqtt
    import paho.mqtt.publish as publish
except ImportError:
    # This part is only required to run the example from within the examples
    # directory when the module itself is not installed.
    #
    # If you have the module installed, just use "import paho.mqtt.client"    
    import inspect
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../src")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
    import paho.mqtt.client as mqtt

logFilePath = '/media/mmcblk0p1/logFile.log'
logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s',filename=logFilePath,level=logging.DEBUG)

f = open('/sys/class/net/eth0/address','r')
mac = f.readline().strip('\n')
f.close()
publishChannel = "server/boardStatus/"+mac
instructionTopic = "board/instruction/#"
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

ip = get_ip_address('eth0')

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))
    mqttc.unsubscribe(instructionTopic)
    mqttc.subscribe(instructionTopic, 0)    

def canExecute(msg):
	fields = msg.split('/')
	for token in fields:
		if token in mac:
			return True
	return False

def on_message(mqttc, obj, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    instruction = str(msg.payload)
    #If is an instruction that all boards must do
    forceToExecute = False
    if(instruction == "discover"):
	    forceToExecute = True
    if(forceToExecute or canExecute(msg.topic)):
	    publish.single(publishChannel,mac+" is executing: "+msg.payload,hostname="148.202.23.200")
	    if(instruction == "exit"):
		    exit()
	    elif instruction=="reboot":
		    command = "/sbin/reboot"
		    process=subprocess.Popen(command.split(), stdout=subprocess.PIPE)
		    output = process.communicate()[0]
		    print output
	    elif instruction == "getIP":
		    publish.single(publishChannel,str(ip),hostname="148.202.23.200")
	    elif "setDate" in instruction:
		    #Split de ':', parametro 0 es la instr y 1 es el datetime
		    dateString = instruction.split(';')[1]
		    print dateString
		    os.system("date "+dateString)
		    #hwclock --systohc --utc
		    os.system("hwclock --systohc --utc")
	    elif "getDate" in instruction:
		    date =  datetime.datetime.now()
		    publish.single(publishChannel,str(date),hostname="148.202.23.200")
	    elif "discover" in instruction:
		    publish.single(publishChannel,"ip;"+str(ip),hostname="148.202.23.200")
	
def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
	publish.single(publishChannel, ip + " suscribed to: board/instruction/"+mac+" at "+str(datetime.datetime.now()),hostname="148.202.23.200")
	print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)
    logging.info(string)

def on_disconnect(client, userdata, rc):
	if rc != 0:
		logging.warning("Unexpected disconnection.")
		mqttc.unsubscribe(instructionTopic)
		print("Unexpected disconnection.")

# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
mqttc.on_log = on_log
mqttc.on_disconnect = on_disconnect
mqttc.connect("148.202.23.200", 1883, 60)

mqttc.loop_forever()

