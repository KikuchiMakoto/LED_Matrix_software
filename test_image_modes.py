"""Test image output modes"""
import time
from src.led_matrix_software.fonts import ShinonomeFont
from src.led_matrix_software.devices import ImageSimulator
from src.led_matrix_software.matrix import make_matrix_buffer
import numpy as np


def test_static_mode():
    """Test static mode - should save single PNG"""
    print("Testing static mode...")
    font = ShinonomeFont()
    device = ImageSimulator(output_dir="output/static")

    text = "静止画"
    img = font.render_string(text)
    matrix = make_matrix_buffer(img)
    device.write(matrix)
    device.close()
    print(f"Static mode: {len(device.frames)} frame(s) saved")


def test_scroll_mode():
    """Test scroll mode - should save MP4 video"""
    print("\nTesting scroll mode...")
    font = ShinonomeFont()
    device = ImageSimulator(output_dir="output/scroll")

    # Simulate scroll with multiple frames
    text = "スクロール"
    img = font.render_string(text)

    # Create multiple frames by shifting
    for i in range(20):
        matrix = make_matrix_buffer(img)
        device.write(matrix)
        # Shift image
        if img.shape[1] > 1:
            img = np.delete(img, 0, axis=1)

    device.close()
    print(f"Scroll mode: {len(device.frames)} frame(s) saved")


if __name__ == '__main__':
    test_static_mode()
    test_scroll_mode()
    print("\nCheck the 'output' directory for results:")
    print("  - output/static/display.png (single image)")
    print("  - output/scroll/animation.mp4 (video)")
