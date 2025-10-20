from machine import Pin, I2C, ADC
from time import sleep
import ssd1306
import network, ujson
from umqtt.simple import MQTTClient

# --- WiFi configuration for Wokwi ---
SSID = "Wokwi-GUEST"   # exact name
PASSWORD = ""           # open network

# --- MQTT configuration ---
MQTT_CLIENT_ID = "esp32-gas-monitor"
MQTT_BROKER = "broker.hivemq.com"   # Public broker
PUB_TOPIC = b"esp32/gas"

# --- Gas sensor setup ---
gas_sensor = ADC(Pin(34))
gas_sensor.atten(ADC.ATTN_11DB)      # Full range 0–3.3V
gas_sensor.width(ADC.WIDTH_12BIT)    # 12-bit resolution (0–4095)

# --- OLED setup ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- Connect WiFi ---
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(SSID, PASSWORD)
while not sta_if.isconnected():
    print(".", end="")
    sleep(0.3)
print("\nConnected! IP:", sta_if.ifconfig()[0])

# --- Connect MQTT ---
print("Connecting to MQTT broker...", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.connect()
print(" connected!")

# --- Main Loop ---
while True:
    raw_value = gas_sensor.read()
    gas_percentage = (raw_value / 4095) * 100

    # Determine status
    if gas_percentage < 40:
        status = "OK"
    elif gas_percentage < 70:
        status = "WARNING"
    else:
        status = "ALERT!"

    # Prepare message
    message = ujson.dumps({
        "gas": gas_percentage,
        "status": status
    })

    # Publish to MQTT broker
    client.publish(PUB_TOPIC, message)
    print("Published:", message)

    # Update OLED display
    oled.fill(0)
    oled.text("ESP32 Gas Monitor", 0, 0)
    oled.text("Gas: {:.1f}%".format(gas_percentage), 0, 20)
    oled.text("Status: {}".format(status), 0, 35)
    oled.text("MQTT: OK", 0, 50)
    oled.show()

    sleep(3)
