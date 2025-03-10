import random
import time

from paho.mqtt import client as mqtt_client



class MqttConn:
        
    # broker = '127.0.0.1'
    broker = '192.168.61.131'
    port = 1883
    # port = 8883
    topic = "topic" #"/python/mqtt"
    # generate client ID with pub prefix randomly
    client_id = f'richard-mqtt'
    client = None

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self.client = mqtt_client.Client(self.client_id)
        self.client.on_connect = on_connect
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    async def publish(self):
        msg_count = 0
        while True:
            time.sleep(1)
            msg = f"messages: {msg_count}"
            result = self.client.publish(self.topic, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{self.topic}`")
            else:
                print(f"Failed to send message to topic {self.topic}")
            msg_count += 1


    async def subscribe(self):
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

        self.client.subscribe(self.topic)
        self.client.on_message = on_message

async def run_mqtt_subscribe(name):
    mqtt_conn = MqttConn()
    mqtt_conn.connect_mqtt()
    await mqtt_conn.subscribe()
    await mqtt_conn.publish()

def run():
    mqttconn = MqttConn()
    mqttconn.connect_mqtt()
    mqttconn.publish()


if __name__ == '__main__':
    run()