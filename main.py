from NFCAttendance import NFCAttendance

from Display import Oled
from time import sleep


try:
    oled = Oled()
    oled.rows[1] = ["GençBilişim", -1]
    oled.rows[3] = ["NFC Yoklama", -1]
    oled.rows[5] = ["Başlatılıyor", -1]
    oled.show(Startup=True)
    connect_wifi()
    set_time()
    sleep(1)
    del oled

    app = NFCAttendance()
except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
