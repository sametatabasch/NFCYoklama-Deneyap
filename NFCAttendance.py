"""
NFC kullanarak yoklama alma işlermleri
"""
from lib.mfrc522 import MFRC522
from machine import Pin, SPI, SoftI2C
import deneyap
import network
import lib.urquest as urequests
import config
from time import sleep, time, gmtime, mktime, ticks_ms, ticks_diff
import ntptime
import json
import lib.ssd1306 as oledFW

wlan = None


def set_time():
    # if needed, overwrite default time server
    ntptime.host = "1.tr.pool.ntp.org"

    try:
        ntptime.settime()
    except Exception as err:
        print("Error syncing time")
        print(err.args)


def tr_time(is_tuple=False):
    """

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


def get_access_key():
    data = {
        "username": config.api_username,
        "password": config.api_passwd
    }
    url = config.api_url + "/login"

    json_data = json.dumps(data)
    response = urequests.post(url, data=json_data, headers={
        'Content-type': 'application/json',
        'Accept': '*/*'
    })

    # İstek sonucunu kontrol etme
    if response.status_code == 200:
        print("Access Token alındı")
        data = response.json()
        # Bağlantıyı kapatma
        response.close()
        return data['access_token']
    else:
        print("İstek başarısız!")
        print(response.json())
        # Bağlantıyı kapatma
        response.close()
        return False


class NFCAttendance():
    '''
        Oled 128x64 px
        font 8x8 px
    '''
    NFC, oled = '',''
    LCD_SPI, NFC_SPI = "", ""
    lcd_rows = [
        ["", -1],
        ["", -1],
        ["", -1],
        ["", -1],
        ["", -1],
        ["", -1],
        ["", -1],
        ["", -1]
    ]
    schedule = {}
    i2c = ''

    def __init__(self):

        pin_miso = Pin(deneyap.MISO)
        pin_mosi = Pin(deneyap.MOSI)
        pin_sck = Pin(deneyap.SCK)

        self.i2c = SoftI2C(sda=Pin(deneyap.SDA), scl=Pin(deneyap.SCL))
        self.oled = oledFW.SSD1306_I2C(128, 64, self.i2c,addr=0x3d)

        self.oled.contrast(255)
        self.oled.invert(1)

        self.NFC_SPI = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        self.NFC_SPI.init()
        self.NFC = MFRC522(spi=self.NFC_SPI, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)


        self.NFC_SPI.deinit()
        self.connect_wifi(self)
        set_time()
        self.get_schedule()
        # start waiting
        self.wait()

    def center(self, msg):
        """
        Find the start x pixel for centering
        :param msg: string to center
        :return int:
        """
        return (128 - len(msg) * 8) // 2 # width of oled is 128 px

    def show_on_screen(self):
        """

        :param rows: list: [[msg, x],... ] for centered text x= -1
        :return:
        """
        self.oled.fill(0) # clear screen
        self.oled.hline(0, 12, 128, 1)  # draw horizontal line x=0, y=12, width=128, colour=1 center of 2. row
        self.oled.hline(0, 52, 128, 1)  # draw horizontal line x=0, y=52, width=128, colour=1 center of 7. row
        row_num = 1
        for row in self.lcd_rows:
            if len(row) > 0:
                startY = ((row_num - 1) * 8)
                self.oled.text(row[0], self.center(row[0]) if row[1] == -1 else row[1], startY if startY!=0 else 1, 1)
            row_num += 1
        self.oled.show()

    def get_schedule(self):
        self.lcd_rows[2] = ["Ders Programi", -1]
        self.lcd_rows[3] = ["", -1]
        self.lcd_rows[4] = ["Aliniyor", -1]
        self.show_on_screen()
        response = urequests.post(config.api_url + "/get_schedule", headers={
            'Content-type': 'application/json',
            'Accept': '*/*',
            'Authorization': "Bearer " + get_access_key()
        })

        # İstek sonucunu kontrol etme
        if response.status_code == 200:
            print("Program alındı")
            data = response.json()
            response.close()
            self.schedule = data['schedule']
            return True
        else:
            print("İstek başarısız!")
            print("Durum kodu = " + response.status_code)
            print(response.json())
            # Bağlantıyı kapatma
            response.close()
            return False

    def check_lesson_time(self):
        """
        It checks if we are at the lesson time and determines the lesson name.
        schedule= {
                    weekday : {
                            "lesson code" : [[startH, startM], [endH, endM]]  ,
                }
        :return: bool

        """
        try:
            day_lessons = self.schedule[str(tr_time()["weekday"])]
            for lesson, times in day_lessons.items():
                '''
                    The start time and end time in the schedule are returned to the mktime(decimal number) type.
                    Because time can be compared more easily in decimal number type.
                '''
                startT = tr_time()
                startT["hour"] = times[0][0]
                startT["minute"] = times[0][1]
                startT = mktime((startT["year"], startT["month"], startT["mday"], startT["hour"], startT["minute"],
                                 startT["second"], startT["weekday"], startT["yearday"]))
                endT = tr_time()
                endT["hour"] = times[1][0]
                endT["minute"] = times[1][1]
                endT = mktime((endT["year"], endT["month"], endT["mday"], endT["hour"], endT["minute"],
                               endT["second"], endT["weekday"], endT["yearday"]))

                if startT <= mktime(tr_time(True)) <= endT:
                    self.lcd_rows[0] = [lesson, -1]  # set lesson name
                    return True
                else:
                    self.lcd_rows[0] = ["", -1]  # clear lesson name
                    return False
        except KeyError as e:
            '''
                If schedule has not this weekday, it throw KeyError
            '''
            self.lcd_rows[0] = ["", -1]  # clear lesson name
            return False

    def read_student_card_uid(self):
        """
        try to read NFC Card id in 10 second
        :return: string uid
        """
        self.lcd_rows[2] = ["Yoklama", -1]
        self.lcd_rows[3] = ["Icin", -1]
        self.lcd_rows[4] = ["Kart Okut", -1]
        self.show_on_screen()
        self.NFC_SPI.init()
        start_time = ticks_ms()
        timeout = 10000  # 10 saniye süreyle okuma yapmaya çalış

        while ticks_diff(ticks_ms(), start_time) < timeout:
            (stat, tag_type) = self.NFC.request(self.NFC.REQIDL)

            if stat == self.NFC.OK:
                (stat, raw_uid) = self.NFC.anticoll()

                if stat == self.NFC.OK:
                    uid = "%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                    self.NFC.stop_crypto1()
                    self.NFC_SPI.deinit()
                    return uid

        # Belirli süre içinde kart okunmadıysa, None değeri döndür
        self.NFC_SPI.deinit()
        return None

    def take_attendance(self):
        std_list = config.std_list

        try:
            std_uid = self.read_student_card_uid()
            if std_uid:
                '''
                    If student card id read
                '''
                print(std_uid)

                self.lcd_rows[2] = ["", -1]
                self.lcd_rows[3] = [std_list.get(std_uid), -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
                sleep(1)  # sleep for showing student info
        except Exception as e:
            print("unregistered student")
            print(e.args)

    def wait(self):
        """
        wait for lesson time
        :return:
        """
        print("wait")
        while True:
            if self.check_lesson_time():
                self.take_attendance()
            else:
                self.lcd_rows[0] = ["", -1]
                self.lcd_rows[2] = ["Ders", -1]
                self.lcd_rows[3] = ["bekleniyor", -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
                sleep(60 * 60 * 5)

    @staticmethod
    def connect_wifi(self):
        global wlan
        wlan = network.WLAN(network.STA_IF)  # create a wlan object
        wlan.active(True)  # Activate the network interface
        wlan.disconnect()  # Disconnect the last connected WiFi
        wlan.connect(config.wifi['ssid'], config.wifi['password'])  # connect wifi
        while (wlan.ifconfig()[0] == '0.0.0.0'):
            self.lcd_rows[2] = ["Internet'e", -1]
            self.lcd_rows[3] = ["Baglaniyor", -1]
            self.lcd_rows[4] = ["", -1]
            self.show_on_screen()
            sleep(1)
            pass
        return True
