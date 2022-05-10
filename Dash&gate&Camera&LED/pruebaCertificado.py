#!/usr/bin/env python
import paho.mqtt.client as mqtt
import ssl, time, inspect, os

# Make sure we're running from project-root regardless where this was invoked from
'''scriptdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
os.chdir(scriptdir)
os.chdir('../../..')
print('WDIR: ' + os.getcwd())'''

broker_address = "classpip.upc.edu"  # this must match the CNAME in your server-cert!
ca_certificate = "ca.crt"
client_certificate = "client.crt"
client_key = "client.key"
topic = "GettingStarted/TLS-CERT-AUTH"


def on_message(client, userdata, message):
    print("message received=", str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)


print("creating new instance")
client = mqtt.Client("mqttclient")

print("connecting to broker")
client.tls_set(ca_certificate, client_certificate, client_key,
               tls_version=ssl.PROTOCOL_TLSv1_2)
client.tls_insecure_set(False)
client.connect(broker_address, 1884, 60)

client.loop_start()

print("Subscribing to topic", topic)
client.on_message = on_message
client.subscribe(topic)

for i in range(1, 10):
    print("Publishing message to topic", topic)
    client.publish(topic, "Hello world from MQTT " + str(i))
    time.sleep(1)

client.loop_stop()

client.disconnect()
print("Goodbye!")