"""LED Matrix Display Main Program"""
import argparse
import time
import sys
from pathlib import Path

import numpy as np

from .fonts import ShinonomeFont, CharaZenkakuFont
from .devices import SerialLEDDevice, TerminalSimulator, ImageSimulator
from .matrix import make_matrix_buffer


def show_text(device, font, text: str):
    """
    Display static text on LED matrix.

    Args:
        device: LED device instance
        font: Font renderer instance
        text: Text to display
    """
    img = font.render_string(text)
    matrix = make_matrix_buffer(img)
    device.write(matrix)


def scroll_text(device, font, text: str, scroll_speed: float = 0.02):
    """
    Scroll text across LED matrix.

    Args:
        device: LED device instance
        font: Font renderer instance
        text: Text to scroll
        scroll_speed: Delay between frames in seconds (default: 0.02)
    """
    # Add padding spaces
    padding = "　　　　　　　　　　　"
    padded_text = padding + text + padding
    img = font.render_string(padded_text)

    # Scroll by removing one column at a time
    loop_length = img.shape[1]
    for i in range(loop_length):
        matrix = make_matrix_buffer(img)
        device.write(matrix)
        img = np.delete(img, 0, axis=1)
        time.sleep(scroll_speed)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='LED Matrix Display Control')

    # Device options
    parser.add_argument(
        '--device',
        choices=['serial', 'terminal', 'image'],
        default='terminal',
        help='Output device type (default: terminal)'
    )
    parser.add_argument(
        '--port',
        default='COM23',
        help='Serial port (for serial device, default: COM23)'
    )
    parser.add_argument(
        '--baudrate',
        type=int,
        default=921600,
        help='Serial baudrate (default: 921600)'
    )

    # Font options
    parser.add_argument(
        '--font',
        choices=['shinonome', 'chara_zenkaku'],
        default='shinonome',
        help='Font to use (default: shinonome)'
    )
    parser.add_argument(
        '--font-dir',
        help='Font directory path (optional)'
    )

    # Display options
    parser.add_argument(
        '--mode',
        choices=['static', 'scroll'],
        default='static',
        help='Display mode (default: static)'
    )
    parser.add_argument(
        '--text',
        default='Hello, LED!',
        help='Text to display'
    )
    parser.add_argument(
        '--scroll-speed',
        type=float,
        default=0.02,
        help='Scroll speed in seconds (default: 0.02)'
    )

    # Image output options
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for image device (default: output)'
    )

    args = parser.parse_args()

    # Initialize font
    print(f"Initializing font: {args.font}")
    if args.font == 'shinonome':
        font_dir = args.font_dir or './shinonome16-1.0.4'
        font = ShinonomeFont(font_dir=font_dir)
    else:  # chara_zenkaku
        font_dir = args.font_dir or './chara_zenkaku'
        font = CharaZenkakuFont(font_dir=font_dir)

    # Initialize device
    print(f"Initializing device: {args.device}")
    if args.device == 'serial':
        try:
            device = SerialLEDDevice(port=args.port, baudrate=args.baudrate)
        except Exception as e:
            print(f"Error: Failed to open serial port {args.port}")
            print(f"Details: {e}")
            print("\nTry using --device terminal for testing without hardware")
            sys.exit(1)
    elif args.device == 'terminal':
        device = TerminalSimulator()
    else:  # image
        device = ImageSimulator(output_dir=args.output_dir)

    try:
        # Display text
        print(f"Displaying text: {args.text}")
        if args.mode == 'static':
            show_text(device, font, args.text)
            if args.device == 'terminal':
                print("\nPress Ctrl+C to exit...")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        else:  # scroll
            scroll_text(device, font, args.text, scroll_speed=args.scroll_speed)

    finally:
        device.close()
        print("\nDone!")


if __name__ == '__main__':
    main()
