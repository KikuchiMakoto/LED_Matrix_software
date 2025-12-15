"""Shinonome 16-pixel font renderer"""
import csv
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from .base import FontRenderer


class ShinonomeFont(FontRenderer):
    """Shinonome 16-pixel Japanese font renderer"""

    class CharacterMapping:
        """Character code mapping"""

        def __init__(self, ver: int, jisx: int, utf8: int):
            self.ver = ver
            self.jisx = jisx
            self.utf8 = utf8

    def __init__(self, font_dir: str = "./shinonome16-1.0.4"):
        """
        Initialize Shinonome font renderer.

        Args:
            font_dir: Path to shinonome font directory
        """
        self.font_dir = Path(font_dir)
        self.zenkaku_map = []
        self._load_character_map()

        # Cache for performance optimization
        self._latin_lines: Optional[List[str]] = None
        self._hankaku_lines: Optional[List[str]] = None
        self._zenkaku_lines: Optional[List[str]] = None
        self._padding_image: Optional[np.ndarray] = None
        self._char_cache: Dict[str, np.ndarray] = {}

    def _load_character_map(self):
        """Load character code mapping from TSV file"""
        tsv_path = self.font_dir / "iso-2022-jp-2004-std.tsv"
        with open(tsv_path, mode="r", encoding="utf-8", newline='') as f:
            reader = csv.reader(f, delimiter="\t")
            # Skip header (23 lines)
            for _ in range(23):
                next(reader)

            for cols in reader:
                try:
                    ver, jisx = cols[0].split("-")
                    utf8 = cols[1].split("+")[1]
                    char = self.CharacterMapping(int(ver), int(jisx, 16), int(utf8, 16))
                    self.zenkaku_map.append(char)
                except (IndexError, ValueError):
                    pass

    def _load_latin_bdf(self) -> List[str]:
        """Load latin.bdf file (cached)"""
        if self._latin_lines is not None:
            return self._latin_lines

        bdf_path = self.font_dir / "latin.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._latin_lines = f.readlines()
        except Exception:
            self._latin_lines = []
        return self._latin_lines

    def _get_latin_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for ASCII character"""
        try:
            ascii_code = int(char.encode('ascii')[0])
        except (UnicodeEncodeError, UnicodeDecodeError):
            return None

        target_string = "STARTCHAR " + format(ascii_code, '2x')
        next_string = "ENCODING " + format(ascii_code, 'd')

        lines = self._load_latin_bdf()
        for i, line in enumerate(lines):
            if line.startswith(target_string) and i + 1 < len(lines) and lines[i + 1].startswith(next_string):
                ret = np.zeros((16, 8, 3), np.uint8)
                for j in range(16):
                    if i + 6 + j < len(lines):
                        line = lines[i + 6 + j]
                        for bit in range(8):
                            if bit < len(line):
                                ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                return ret
        return None

    def _load_hankaku_bdf(self) -> List[str]:
        """Load hankaku.bdf file (cached)"""
        if self._hankaku_lines is not None:
            return self._hankaku_lines

        bdf_path = self.font_dir / "hankaku.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._hankaku_lines = f.readlines()
        except Exception:
            self._hankaku_lines = []
        return self._hankaku_lines

    def _get_hankaku_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for half-width character"""
        try:
            sjis = int(char.encode('shift_jis')[0])
        except (UnicodeEncodeError, UnicodeDecodeError):
            return None

        target_string = "STARTCHAR   " + format(sjis, '2x')

        lines = self._load_hankaku_bdf()
        for i, line in enumerate(lines):
            if line.startswith(target_string):
                ret = np.zeros((16, 8, 3), np.uint8)
                for j in range(16):
                    if i + 6 + j < len(lines):
                        line = lines[i + 6 + j]
                        for bit in range(8):
                            if bit < len(line):
                                ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                return ret
        return None

    def _load_zenkaku_bdf(self) -> List[str]:
        """Load zenkaku.bdf file (cached)"""
        if self._zenkaku_lines is not None:
            return self._zenkaku_lines

        bdf_path = self.font_dir / "zenkaku.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._zenkaku_lines = f.readlines()
        except Exception:
            self._zenkaku_lines = []
        return self._zenkaku_lines

    def _get_zenkaku_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for full-width character"""
        jisx = None
        for c in self.zenkaku_map:
            if c.utf8 == ord(char):
                jisx = c.jisx
                break

        if jisx is None:
            return None

        target_string = "STARTCHAR " + format(jisx, '4x')

        lines = self._load_zenkaku_bdf()
        for i, line in enumerate(lines):
            if line.startswith(target_string):
                ret = np.zeros((16, 16, 3), np.uint8)
                for j in range(16):
                    if i + 6 + j < len(lines):
                        line = lines[i + 6 + j]
                        for bit in range(16):
                            if bit < len(line):
                                ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                return ret
        return None

    def get_char_image(self, char: str) -> Optional[np.ndarray]:
        """
        Get image for a single character based on its width type.

        Args:
            char: Single character

        Returns:
            Character image (16x8 or 16x16) or None if not found
        """
        # Check cache first
        if char in self._char_cache:
            return self._char_cache[char]

        width_type = unicodedata.east_asian_width(char)

        char_img = None
        if width_type == 'Na':  # Narrow (ASCII)
            char_img = self._get_latin_image(char)
        elif width_type in ('F', 'W'):  # Fullwidth or Wide
            char_img = self._get_zenkaku_image(char)
        elif width_type == 'H':  # Halfwidth
            char_img = self._get_hankaku_image(char)

        # Cache the result (even if None)
        if char_img is not None:
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
