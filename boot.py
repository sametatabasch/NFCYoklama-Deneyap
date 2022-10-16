# boot.py -- run on boot-up
import NFCRead
import NFCWrite
import config
import network
import time

wlan = None


def connect_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)  # create a wlan object
    wlan.active(True)  # Activate the network interface
    wlan.disconnect()  # Disconnect the last connected WiFi
    wlan.connect(config.wifi['ssid'], config.wifi['password'])  # connect wifi
    while (wlan.ifconfig()[0] == '0.0.0.0'):
        time.sleep(1)
        pass
    return True


connect_wifi()

while True:
    islem = input("İşlem seçin: 1- Okuma, 2- Yazma, 0- çıkış")
    if(islem =='1'):
        NFCRead.do_read()
    elif(islem=='2'):
        NFCWrite.do_write()
    else:
        break

