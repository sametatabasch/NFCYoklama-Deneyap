# boot.py -- run on boot-up
import ntptime
from time import time, gmtime, sleep, ticks_ms, ticks_diff

import network
import config

def connect_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()

    for network_config in config.wifi:
        print("Bağlanmaya çalışılan ağ:", network_config['ssid'])
        wlan.connect(network_config['ssid'], network_config.get('password'))

        start_time = ticks_ms()
        timeout = 10000  # 10 saniye süreyle okuma yapmaya çalış

        while (wlan.ifconfig()[0] == '0.0.0.0') and ticks_diff(ticks_ms(), start_time) < timeout:
            print("İnternete Bağlanılıyor.")
            sleep(1)

        if wlan.isconnected():
            print("Bağlantı başarılı! IP adresi:", wlan.ifconfig()[0])
            return True
        else:
            print("Bağlantı başarısız. Diğer ağı deneyin.")
            wlan.disconnect()

    print("Bağlantı başarısız.")
    return False


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
