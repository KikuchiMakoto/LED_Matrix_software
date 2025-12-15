"""Chara Zenkaku font renderer"""
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from .base import FontRenderer


class CharaZenkakuFont(FontRenderer):
    """Chara Zenkaku 16-pixel Japanese font renderer"""

    def __init__(self, font_dir: str = "./chara_zenkaku"):
        """
        Initialize Chara Zenkaku font renderer.

        Args:
            font_dir: Path to chara_zenkaku font directory
        """
        self.font_dir = Path(font_dir)
        self.x_offset = 50
        self.y_offset = 50
        self.x_step = 17
        self.y_step = 17
        self.char_width = 16
        self.char_height = 16

        # Cache for performance optimization
        self._char_map: Optional[Dict[str, Tuple[int, int]]] = None
        self._font_image: Optional[np.ndarray] = None
        self._padding_image: Optional[np.ndarray] = None
        self._char_cache: Dict[str, np.ndarray] = {}

    def _load_char_map(self) -> Dict[str, Tuple[int, int]]:
        """
        Load character map from file (cached).

        Returns:
            Dictionary mapping characters to (line, column) positions
        """
        if self._char_map is not None:
            return self._char_map

        self._char_map = {}
        txt_path = self.font_dir / 'chara_zenkaku.txt'
        try:
            with open(txt_path, mode='r', encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    for j, char in enumerate(line):
                        if char not in ('\n', '\r'):
                            self._char_map[char] = (i, j)
        except FileNotFoundError:
            pass
        return self._char_map

    def _find_char_position(self, char: str) -> Optional[Tuple[int, int]]:
        """
        Find character position in character map.

        Args:
            char: Single character

        Returns:
            (line, column) position or None if not found
        """
        char_map = self._load_char_map()
        return char_map.get(char)

    def _load_font_image(self) -> Optional[np.ndarray]:
        """
        Load font image (cached).

        Returns:
            Font image or None if not found
        """
        if self._font_image is not None:
            return self._font_image

        png_path = self.font_dir / 'chara_zenkaku.png'
        try:
            self._font_image = cv2.imread(str(png_path))
        except Exception:
            pass
        return self._font_image

    def get_char_image(self, char: str) -> Optional[np.ndarray]:
        """
        Get image for a single character.

        Args:
            char: Single character

        Returns:
            Character image (16x16) or None if not found
        """
        # Check cache first
        if char in self._char_cache:
            return self._char_cache[char]

        pos = self._find_char_position(char)
        if pos is None:
            return None

        line, num = pos
        img = self._load_font_image()
        if img is None:
            return None

        x = self.x_offset + num * self.x_step
        y = self.y_offset + line * self.y_step
        char_img = img[y:y + self.char_height, x:x + self.char_width].copy()

        # Cache the character image
        self._char_cache[char] = char_img
        return char_img

    def _load_padding_image(self) -> Optional[np.ndarray]:
        """
        Load padding image (cached).

        Returns:
            Padding image or None if not found
        """
        if self._padding_image is not None:
            return self._padding_image

        try:
            self._padding_image = cv2.imread(str(self.font_dir / 'padding.bmp'))
        except Exception:
            pass
        return self._padding_image

    def render_string(self, text: str) -> np.ndarray:
        """
        Render text string to binary image.

        Args:
            text: Text to render

        Returns:
            Binary image (height=16, variable width)
        """
        # Get padding image once
        padding = self._load_padding_image()

        # Collect all character images first
        char_images = []
        for char in text:
            char_img = self.get_char_image(char)
            if char_img is not None:
                char_images.append(char_img)

        if not char_images:
            # Return empty image if no characters were rendered
            return np.zeros((16, 0), dtype=np.uint8)

        # Concatenate all images at once using numpy for better performance
        if padding is not None and len(char_images) > 1:
            # Interleave character images with padding
            images_with_padding = []
            for i, img in enumerate(char_images):
                images_with_padding.append(img)
                if i < len(char_images) - 1:
                    images_with_padding.append(padding)
            merged_image = cv2.hconcat(images_with_padding)
        else:
            merged_image = cv2.hconcat(char_images) if len(char_images) > 1 else char_images[0]

        # Convert to grayscale
        merged_image = cv2.cvtColor(merged_image, cv2.COLOR_BGR2GRAY)
        # Binarize
        _, merged_image = cv2.threshold(merged_image, 128, 255, cv2.THRESH_BINARY)

        return merged_image
