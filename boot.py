# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()


    app.read_student_card()
    app.LCD.clear()
except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
