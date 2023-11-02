from machine import Pin
from time import sleep, ticks_ms, ticks_diff
import deneyap,config


class Keypad:

    def __init__(self):
        # Create a map between keypad buttons and characters
        self.matrix_keys = [['1', '2', '3', 'A'],
                            ['4', '5', '6', 'B'],
                            ['7', '8', '9', 'C'],
                            ['*', '0', '#', 'D']]

        # PINs according to schematic - Change the pins to match with your connections
        keypad_rows = [
            config.Keypad.get("row1"),
            config.Keypad.get("row2"),
            config.Keypad.get("row3"),
            config.Keypad.get("row4")]
        keypad_columns = [
            config.Keypad.get("col1"),
            config.Keypad.get("col2"),
            config.Keypad.get("col3"),
            config.Keypad.get("col4")]

        # Create two empty lists to set up pins ( Rows output and columns input )
        self.col_pins = []
        self.row_pins = []

        # Loop to assign GPIO pins and setup input and outputs
        for x in range(0, 4):
            self.row_pins.append(Pin(keypad_rows[x], Pin.OUT))
            self.row_pins[x].value(1)
            self.col_pins.append(Pin(keypad_columns[x], Pin.IN, Pin.PULL_DOWN))
            self.col_pins[x].value(0)
        self.pressed_key = None

    def scankeys(self):
        for row in range(4):
            for col in range(4):
                self.row_pins[row].on()

                if self.col_pins[col].value() == 1:
                    print("You have pressed:", self.matrix_keys[row][col])
                    self.pressed_key = self.matrix_keys[row][col]
                    sleep(0.5)
                    return

            self.row_pins[row].off()

    def get_key(self, timeout: int = None):
        """
        Get one char from Keypad
        :param timeout: time out in millisecond(ms)
        :return str| None: Pressed key value
        """
        timeout = 0 if timeout is None else timeout
        start_time = ticks_ms()
        while self.pressed_key is None and (ticks_diff(ticks_ms(), start_time) < timeout or timeout == 0):
            self.scankeys()
        key = self.pressed_key
        self.pressed_key = None
        return key

    def get_keys(self, count: int, timeout: int = None):
        """

        :param count: Number of wanted keys
        :param timeout: time out in millisecond(ms) for each key
        :return list: list of keys
        """
        keys = []
        for i in range(count):
            keys.append(self.get_key(timeout))

        return keys
