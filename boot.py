# boot.py -- run on boot-up
import ntptime
from time import time, gmtime, localtime

import network
import config
from time import sleep

def connect_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)  # create a wlan object
    wlan.active(True)  # Activate the network interface
    wlan.disconnect()  # Disconnect the last connected WiFi
    wlan.connect(config.wifi['ssid'], config.wifi['password'])  # connect wifi
    while (wlan.ifconfig()[0] == '0.0.0.0'):
        print("İnternete Bağlanılıyor.")
        sleep(1)
        pass
    return True


def set_time():
    # if needed, overwrite default time server
    ntptime.host = "1.tr.pool.ntp.org"
    ntptime.timezone = 3
    try:
        ntptime.settime()
        print("Set Time")
        print(gmtime())
    except Exception as err:
        print("Error syncing time")
        print(err.args)


def tr_time(is_tuple=False):
    """
        Return UTC+3 time
        :return: tuple (year, month, mday, hour, minute, second, weekday, yearday)
    """
    tm = gmtime(time() + 10800)  # UTC+3

    return tm if is_tuple else {
        "year": tm[0],
        "month": tm[1],
        "mday": tm[2],
        "hour": tm[3],
        "minute": tm[4],
        "second": tm[5],
        "weekday": tm[6],
        "yearday": tm[7]
    }
