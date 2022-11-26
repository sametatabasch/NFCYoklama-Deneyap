# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()
except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
