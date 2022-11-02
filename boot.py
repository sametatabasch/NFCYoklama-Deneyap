# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()
    lcd_rows = [
        ['BILP-100', -1],
        ["----------",-1],
        ["Yoklama", -1],
        ["Icin",-1],
        ["Kart Okut",-1],
        ["----------",-1]
    ]
    app.show_lcd(lcd_rows)

    # app.read_student_card()

except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
