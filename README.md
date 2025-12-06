# LED Matrix Software

16ピクセル高のLEDマトリックスディスプレイ（128x16）を制御するPythonソフトウェアです。

## 特徴

- **複数のフォント対応**
  - Shinonomeフォント（推奨）: 豊富な日本語文字、ひらがな、カタカナ、漢字対応
  - Chara Zenkakuフォント: 全角文字対応

- **複数の出力デバイス対応**
  - シリアルデバイス: 実際のLEDマトリックス（シリアル接続）
  - ターミナル出力: ハードウェアなしでテスト可能
  - 画像出力: staticモードではPNG画像、scrollモードではMP4動画として保存

- **表示モード**
  - 静的表示: テキストを固定表示
  - スクロール表示: テキストを右から左にスクロール

## インストール

### 前提条件

- Python 3.11以上
- uv（推奨）

### uvを使用したインストール

```bash
# 依存関係のインストール
uv sync

# 開発モードでインストール
uv pip install -e .
```

### 通常のpipを使用したインストール

```bash
pip install -e .
```

## 使い方

### 基本的な使い方

```bash
# ターミナルでテキストを表示（デフォルト）
uv run python -m led_matrix_software.main --text "こんにちは"

# スクロール表示
uv run python -m led_matrix_software.main --mode scroll --text "LEDマトリックスディスプレイ"

# 静的表示を画像として保存（PNG形式）
uv run python -m led_matrix_software.main --device image --text "Hello LED"

# スクロール表示を動画として保存（MP4形式）
uv run python -m led_matrix_software.main --device image --mode scroll --text "テスト"
```

### シリアルデバイスの使用

```bash
# Windows
uv run python -m led_matrix_software.main --device serial --port COM23 --text "Hello"

# Linux/Mac
uv run python -m led_matrix_software.main --device serial --port /dev/ttyUSB0 --text "Hello"
```

### フォントの選択

```bash
# Shinonomeフォント（デフォルト）
uv run python -m led_matrix_software.main --font shinonome --text "東京スカイツリー"

# Chara Zenkakuフォント
uv run python -m led_matrix_software.main --font chara_zenkaku --text "あけましておめでとう"
```

### コマンドラインオプション

```
--device {serial,terminal,image}  出力デバイスタイプ（デフォルト: terminal）
--port PORT                       シリアルポート（デフォルト: COM23）
--baudrate BAUDRATE               ボーレート（デフォルト: 921600）
--font {shinonome,chara_zenkaku}  使用するフォント（デフォルト: shinonome）
--font-dir FONT_DIR               フォントディレクトリパス
--mode {static,scroll}            表示モード（デフォルト: static）
--text TEXT                       表示するテキスト
--scroll-speed SPEED              スクロール速度（秒）（デフォルト: 0.02）
--output-dir OUTPUT_DIR           画像出力ディレクトリ（デフォルト: output）
```

## プロジェクト構造

```
led-matrix-software/
├── src/
│   └── led_matrix_software/
│       ├── __init__.py
│       ├── main.py              # メインエントリーポイント
│       ├── matrix.py            # マトリックスバッファ変換
│       ├── devices/             # デバイスモジュール
│       │   ├── __init__.py
│       │   ├── base.py          # デバイス基底クラス
│       │   ├── serial_device.py # シリアルデバイス
│       │   └── simulator.py     # シミュレータ（ターミナル/画像）
│       └── fonts/               # フォントモジュール
│           ├── __init__.py
│           ├── base.py          # フォント基底クラス
│           ├── shinonome.py     # Shinonomeフォント
│           └── chara_zenkaku.py # Chara Zenkakuフォント
├── shinonome16-1.0.4/           # Shinonomeフォントデータ
├── chara_zenkaku/               # Chara Zenkakuフォントデータ
├── pyproject.toml               # プロジェクト設定
└── README.md
```

## LEDマトリックス仕様

- **解像度**: 128 x 16 ピクセル
- **通信**: シリアル通信（921600 bps）
- **プロトコル**: Base64エンコードされた256バイト（uint16配列[8][16]）
- **ファームウェア**: [LED_Matrix_firmware_K00798](https://github.com/KikuchiMakoto/LED_Matrix_firmware_K00798)

## 開発

### テスト実行

```bash
# ターミナルシミュレータでテスト
uv run python -m led_matrix_software.main --device terminal --text "テスト"
```

### コードフォーマット

```bash
uv run black src/
uv run ruff check src/
```

## ライセンス

このプロジェクトは個人使用を目的としています。
