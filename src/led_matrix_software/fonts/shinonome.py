"""Shinonome 16-pixel font renderer with BDF indexing optimization"""
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

        # Cache for performance optimization
        self._latin_lines: Optional[List[str]] = None
        self._hankaku_lines: Optional[List[str]] = None
        self._zenkaku_lines: Optional[List[str]] = None
        self._padding_image: Optional[np.ndarray] = None
        self._char_cache: Dict[str, np.ndarray] = {}

        # BDF index cache (maps character code to line number for fast lookup)
        self._latin_index: Optional[Dict[str, int]] = None
        self._hankaku_index: Optional[Dict[str, int]] = None
        self._zenkaku_index: Optional[Dict[str, int]] = None

        # UTF8 to JISX code map for fast zenkaku character lookup
        self._utf8_to_jisx: Optional[Dict[int, int]] = None

        # Load character mapping after initializing all attributes
        self._load_character_map()

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

        # Build UTF8 to JISX map for faster lookup
        if self._utf8_to_jisx is None:
            self._utf8_to_jisx = {c.utf8: c.jisx for c in self.zenkaku_map}

    def _build_bdf_index(self, lines: List[str]) -> Dict[str, int]:
        """
        Build index mapping character codes to line numbers in BDF file.

        Args:
            lines: BDF file lines

        Returns:
            Dictionary mapping character code (e.g., "3042") to line number
        """
        index = {}
        for i, line in enumerate(lines):
            if line.startswith('STARTCHAR'):
                parts = line.split()
                if len(parts) >= 2:
                    char_code = parts[1].strip()
                    index[char_code] = i
        return index

    def _load_latin_bdf(self) -> List[str]:
        """Load latin.bdf file (cached)"""
        # Check if already loaded successfully (non-empty)
        if self._latin_lines is not None and len(self._latin_lines) > 0:
            return self._latin_lines

        bdf_path = self.font_dir / "latin.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._latin_lines = f.readlines()

            # Build index for fast lookup (skip expensive data preprocessing)
            if len(self._latin_lines) > 0:
                self._latin_index = self._build_bdf_index(self._latin_lines)
        except Exception:
            self._latin_lines = []
        return self._latin_lines

    def _get_latin_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for ASCII character (optimized with BDF index)"""
        try:
            ascii_code = int(char.encode('ascii')[0])
        except (UnicodeEncodeError, UnicodeDecodeError):
            return None

        char_code = format(ascii_code, '2x')
        lines = self._load_latin_bdf()

        # Use index for fast lookup if available
        if self._latin_index:
            line_num = self._latin_index.get(char_code)
            if line_num is not None and line_num + 1 < len(lines):
                next_string = "ENCODING " + format(ascii_code, 'd')
                if lines[line_num + 1].startswith(next_string):
                    # Generate bitmap using index (skip linear search)
                    ret = np.zeros((16, 8, 3), np.uint8)
                    for j in range(16):
                        if line_num + 6 + j < len(lines):
                            line = lines[line_num + 6 + j]
                            for bit in range(8):
                                if bit < len(line):
                                    ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                    return ret

        # Fallback: Linear search if index not available
        target_string = "STARTCHAR " + char_code
        next_string = "ENCODING " + format(ascii_code, 'd')

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
        # Check if already loaded successfully (non-empty)
        if self._hankaku_lines is not None and len(self._hankaku_lines) > 0:
            return self._hankaku_lines

        bdf_path = self.font_dir / "hankaku.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._hankaku_lines = f.readlines()

            # Build index for fast lookup (skip expensive data preprocessing)
            if len(self._hankaku_lines) > 0:
                self._hankaku_index = self._build_bdf_index(self._hankaku_lines)
        except Exception:
            self._hankaku_lines = []
        return self._hankaku_lines

    def _get_hankaku_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for half-width character (optimized with BDF index)"""
        try:
            sjis = int(char.encode('shift_jis')[0])
        except (UnicodeEncodeError, UnicodeDecodeError):
            return None

        char_code = format(sjis, '2x')
        lines = self._load_hankaku_bdf()

        # Use index for fast lookup if available
        if self._hankaku_index:
            # Try with extra spaces (BDF format uses "STARTCHAR   XX")
            for prefix in ["  ", " ", ""]:
                lookup_code = prefix + char_code
                line_num = self._hankaku_index.get(lookup_code)
                if line_num is not None and line_num + 6 + 16 <= len(lines):
                    # Generate bitmap using index (skip linear search)
                    ret = np.zeros((16, 8, 3), np.uint8)
                    for j in range(16):
                        if line_num + 6 + j < len(lines):
                            line = lines[line_num + 6 + j]
                            for bit in range(8):
                                if bit < len(line):
                                    ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                    return ret

        # Fallback: Linear search if index not available
        target_string = "STARTCHAR   " + char_code

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
        # Check if already loaded successfully (non-empty)
        if self._zenkaku_lines is not None and len(self._zenkaku_lines) > 0:
            return self._zenkaku_lines

        bdf_path = self.font_dir / "zenkaku.bdf"
        try:
            with open(bdf_path, mode="r", encoding="utf-8") as f:
                self._zenkaku_lines = f.readlines()

            # Build index for fast lookup (skip expensive data preprocessing)
            if len(self._zenkaku_lines) > 0:
                self._zenkaku_index = self._build_bdf_index(self._zenkaku_lines)
        except Exception:
            self._zenkaku_lines = []
        return self._zenkaku_lines

    def _get_zenkaku_image(self, char: str) -> Optional[np.ndarray]:
        """Get image for full-width character (optimized with BDF index)"""
        # Use fast UTF8 to JISX lookup
        if self._utf8_to_jisx:
            jisx = self._utf8_to_jisx.get(ord(char))
        else:
            jisx = None
            for c in self.zenkaku_map:
                if c.utf8 == ord(char):
                    jisx = c.jisx
                    break

        if jisx is None:
            return None

        char_code = format(jisx, '4x')
        lines = self._load_zenkaku_bdf()

        # Use index for fast lookup if available
        if self._zenkaku_index:
            line_num = self._zenkaku_index.get(char_code)
            if line_num is not None and line_num + 6 + 16 <= len(lines):
                # Generate bitmap using index (skip linear search)
                ret = np.zeros((16, 16, 3), np.uint8)
                for j in range(16):
                    if line_num + 6 + j < len(lines):
                        line = lines[line_num + 6 + j]
                        for bit in range(16):
                            if bit < len(line):
                                ret[j][bit] = [0, 0, 0] if line[bit] == "." else [255, 255, 255]
                return ret

        # Fallback: Linear search if index not available
        target_string = "STARTCHAR " + char_code

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
