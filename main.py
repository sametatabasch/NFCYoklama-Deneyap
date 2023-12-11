import sys

from NFCAttendance import NFCAttendance

from Display import Oled
from time import sleep


try:
    oled = Oled()
    oled.rows[1] = ["GençBilişim", -1]
    oled.rows[3] = ["NFC Yoklama", -1]
    oled.rows[5] = ["Başlatılıyor", -1]
    oled.show(startup=True)
    c= connect_wifi()
    if not c:
        oled.rows[1] = ["Bağlantı ", -1]
        oled.rows[3] = ["Kurulamadı", -1]
        oled.rows[5] = ["Yeniden başlat", -1]
        oled.show(startup=True)
        sys.exit()
    set_time()
    sleep(1)
    del oled

    app = NFCAttendance()
except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
    oled = Oled()
    oled.show()
