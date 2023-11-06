import lib.deneyap as deneyap

wifi = [
    {
        'ssid': '',
        'password': ""
    },
    {
        'ssid': '',
        'password': ""
    }
]

api_username = ""
api_passwd = ""
api_url = ""

Buzzer = {
    "buzzer_pin": deneyap.A4,
}
Keypad ={
    "row1": deneyap.D12,
    "row2": deneyap.D13,
    "row3": deneyap.D14,
    "row4": deneyap.D15,
    "col1": deneyap.DAC2,
    "col2": deneyap.DAC1,
    "col3": deneyap.A5,
    "col4": deneyap.D4,
}

Display = {
    "i2c_address": 0x3d,
    "SDA": deneyap.SDA,
    "SCL": deneyap.SCL,
    "width":128,
    "height":64
}

NFC = {
    "miso": deneyap.MISO,
    "mosi": deneyap.MOSI,
    "sck": deneyap.SCK,
    "rst": deneyap.D0,
    "cs": deneyap.D1,
}