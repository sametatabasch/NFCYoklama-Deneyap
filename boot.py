# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()
    app.show_lcd()

    app.read_student_card()

except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
