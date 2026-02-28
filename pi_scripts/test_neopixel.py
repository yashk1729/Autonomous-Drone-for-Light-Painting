import time
import board
import neopixel

LED_PIN = board.D18      # GPIO18 (physical pin 12)
LED_COUNT = 25           # number of LEDs on your strip

pixels = neopixel.NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=1.0,      # max brightness for testing
    auto_write=True,
    pixel_order=neopixel.GRB,
)

print("Starting test: RED -> GREEN -> BLUE -> OFF, looping...")

try:
    while True:
        pixels.fill((255, 0, 0))   # RED
        time.sleep(1.0)
        pixels.fill((0, 255, 0))   # GREEN
        time.sleep(1.0)
        pixels.fill((0, 0, 255))   # BLUE
        time.sleep(1.0)
        pixels.fill((0, 0, 0))     # OFF
        time.sleep(1.0)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    print("Test stopped, LEDs off.")
