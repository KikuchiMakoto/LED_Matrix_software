"""LED Matrix Display - Main Entry Point

This script demonstrates how to use the LED Matrix software with the refactored
module structure. It supports static display, single scroll, and infinite loop scrolling.

Usage:
    # Static display
    python main.py --text "Hello"

    # Scroll mode (single scroll)
    python main.py --mode scroll --text "スクロール"

    # Loop mode (infinite loop until Ctrl+C)
    python main.py --mode loop --text "ループ"

    # Using different devices
    python main.py --device serial --port COM23 --text "Test"
    python main.py --device terminal --text "Test"
    python main.py --device image --output-dir output --text "Test"

    # Note: For image device, loop mode will behave as scroll mode (single scroll)
    python main.py --device image --mode loop --text "Test"
"""
import argparse
import sys

from src.led_matrix_software.fonts import ShinonomeFont, CharaZenkakuFont
from src.led_matrix_software.devices import SerialLEDDevice, TerminalSimulator, ImageSimulator
from src.led_matrix_software.main import show_text, scroll_text, loop_text


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LED Matrix Display Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --text "Hello, World!"
  %(prog)s --mode scroll --text "スクロールテスト"
  %(prog)s --mode loop --text "ループテスト"
  %(prog)s --device serial --port COM23 --text "Test"
  %(prog)s --device image --output-dir output --mode scroll --text "動画"
  %(prog)s --device image --output-dir output --mode loop --text "ループ動画"
        """
    )

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
        choices=['static', 'scroll', 'loop'],
        default='static',
        help='Display mode: static (no scroll), scroll (scroll once), loop (infinite scroll, default: static)'
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
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        elif args.mode == 'scroll':
            scroll_text(device, font, args.text, scroll_speed=args.scroll_speed)
        else:  # loop
            # For image device, loop mode behaves as scroll mode (single scroll)
            if args.device == 'image':
                print("Image device detected: loop mode will behave as scroll mode (single scroll)")
                scroll_text(device, font, args.text, scroll_speed=args.scroll_speed)
            else:
                loop_text(device, font, args.text, scroll_speed=args.scroll_speed)

    finally:
        device.close()
        print("\nDone!")


if __name__ == '__main__':
    main()
