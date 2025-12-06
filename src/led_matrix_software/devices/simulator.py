"""LED Matrix Simulator - Terminal and Image output"""
import os
import sys
import numpy as np
import cv2
from pathlib import Path

from .base import LEDDevice


class TerminalSimulator(LEDDevice):
    """Simulated LED matrix device with terminal output"""

    def __init__(self, use_unicode: bool = True):
        """
        Initialize terminal simulator.

        Args:
            use_unicode: Use Unicode block characters for better display (default: True)
        """
        self.width = 128  # 8 columns * 16 bits
        self.height = 16
        self.use_unicode = use_unicode
        self.frame_count = 0

    def write(self, matrix_buffer: np.ndarray) -> None:
        """
        Display matrix buffer in terminal.

        Args:
            matrix_buffer: uint16 array [8][16]
        """
        # Clear screen
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')

        print(f"\n=== LED Matrix Simulator (Frame {self.frame_count}) ===")
        print("+" + "-" * self.width + "+")

        for y in range(self.height):
            row = "|"
            for x in range(self.width):
                col_idx = x // 16
                bit_idx = x % 16
                value = matrix_buffer[col_idx][y]
                is_on = (value >> (15 - bit_idx)) & 1

                if self.use_unicode:
                    row += "█" if is_on else " "
                else:
                    row += "#" if is_on else " "
            row += "|"
            print(row)

        print("+" + "-" * self.width + "+")
        self.frame_count += 1

    def close(self) -> None:
        """No resources to close for terminal output"""
        pass


class ImageSimulator(LEDDevice):
    """Simulated LED matrix device with image file output"""

    def __init__(self, output_dir: str = "output", pixel_size: int = 10):
        """
        Initialize image simulator.

        Args:
            output_dir: Directory to save output images (default: 'output')
            pixel_size: Size of each LED pixel (default: 10)
        """
        self.width = 128  # 8 columns * 16 bits
        self.height = 16
        self.pixel_size = pixel_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.frame_count = 0
        self.frames = []

    def write(self, matrix_buffer: np.ndarray) -> None:
        """
        Save matrix buffer as image file.

        Args:
            matrix_buffer: uint16 array [8][16]
        """
        # Create image
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        for y in range(self.height):
            for x in range(self.width):
                col_idx = x // 16
                bit_idx = x % 16
                value = matrix_buffer[col_idx][y]
                is_on = (value >> (15 - bit_idx)) & 1

                if is_on:
                    img[y, x] = [0, 0, 255]  # Red LED

        # Scale up
        img = cv2.resize(
            img,
            (self.width * self.pixel_size, self.height * self.pixel_size),
            interpolation=cv2.INTER_NEAREST
        )

        # Save frame
        output_file = self.output_dir / f"frame_{self.frame_count:04d}.png"
        cv2.imwrite(str(output_file), img)
        self.frames.append(img)
        self.frame_count += 1

    def save_gif(self, filename: str = "animation.gif", fps: int = 30) -> None:
        """
        Save all frames as animated GIF.

        Args:
            filename: Output GIF filename
            fps: Frames per second
        """
        if not self.frames:
            return

        output_path = self.output_dir / filename
        # OpenCV doesn't support GIF directly, so save as video instead
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width = self.frames[0].shape[:2]
        out = cv2.VideoWriter(
            str(output_path.with_suffix('.mp4')),
            fourcc,
            fps,
            (width, height)
        )

        for frame in self.frames:
            out.write(frame)

        out.release()
        print(f"Animation saved to {output_path.with_suffix('.mp4')}")

    def close(self) -> None:
        """Save animation on close"""
        if self.frames:
            self.save_gif()


# Alias for backward compatibility
SimulatorDevice = TerminalSimulator
