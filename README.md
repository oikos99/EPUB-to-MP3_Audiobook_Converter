# EPUB to MP3 Audiobook Converter

Convert EPUB books into chapter-by-chapter MP3 files using Microsoft Edge neural text-to-speech voices.

This repo is designed for personal audiobook generation from EPUB files, especially Traditional Chinese / Taiwan Mandarin books. It also supports U.S. English voices.

## Features

- Converts `.epub` files into `.mp3` audio
- Extracts text from EPUB XHTML files in spine order
- Splits long chapters into smaller TTS-safe chunks
- Supports Taiwan Mandarin voice presets
- Supports U.S. English voice presets
- Lets you pass any raw Edge TTS voice name
- Skips already-generated MP3 files so interrupted runs can resume
- Works in a project-local Python virtual environment
- Can be run directly as a Python script or installed as a local CLI
- No Docker required

## Voice Presets

| Preset | Voice | Language / Region | Gender |
|---|---|---|---|
| `tw-female` | `zh-TW-HsiaoChenNeural` | Taiwan Mandarin | Female |
| `tw-female-2` | `zh-TW-HsiaoYuNeural` | Taiwan Mandarin | Female |
| `tw-male` | `zh-TW-YunJheNeural` | Taiwan Mandarin | Male |
| `us-female` | `en-US-JennyNeural` | U.S. English | Female |
| `us-female-2` | `en-US-AvaNeural` | U.S. English | Female |
| `us-male` | `en-US-GuyNeural` | U.S. English | Male |

`en-US` means English (United States). `zh-TW` means Taiwanese Mandarin / Traditional Chinese.

Use Taiwan Mandarin voices for Chinese EPUBs and U.S. English voices for English EPUBs. English voices can read Chinese text, but pronunciation will usually be poor.

You can also pass any valid Edge TTS voice name directly.

To list available voices:

```bash
python epub_to_mp3.py --list-voices
```

or, after installing the local CLI:

```bash
epub-to-mp3 --list-voices
```

## Project Structure

```text
epub-to-mp3-audiobook-converter/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── LICENSE
├── epub_to_mp3.py
├── books/
│   └── .gitkeep
└── mp3_output/
    └── .gitkeep
```

Put your EPUB files inside `books/`. Generated MP3 files are written to `mp3_output/` by default.

The `.gitignore` file is configured to keep `books/` and `mp3_output/` in the repo while ignoring actual `.epub` and generated audio files.

## Setup

Open a terminal in the project root folder. The project root is the folder that contains `README.md`, `requirements.txt`, and `epub_to_mp3.py`.

For example:

```bash
cd /path/to/your/project-folder
```

Create a project-local virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

You should now see `(.venv)` in your terminal prompt.

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

This installs packages only inside the project’s `.venv` folder. It does **not** install packages globally on your system.

To deactivate the virtual environment later:

```bash
deactivate
```

Do not commit `.venv/` to GitHub. It is listed in `.gitignore`.

## Optional: Install as a Local CLI

The script can also be installed in editable mode so you can run it as `epub-to-mp3` instead of typing `python epub_to_mp3.py`.

With the virtual environment activated, run:

```bash
python -m pip install -e .
```

Then use:

```bash
epub-to-mp3 "books/your-book.epub" --voice tw-female
```

This still installs only inside the active `.venv`.

## PyCharm Setup

Open the repo folder in PyCharm.

Then go to:

```text
PyCharm → Settings → Project → Python Interpreter
```

Choose or create the interpreter inside this project:

```text
.venv/bin/python
```

On macOS it will look similar to:

```text
/Users/yourname/path/to/project-folder/.venv/bin/python
```

If you have not created `.venv` yet, create it in PyCharm using:

```text
Project venv → Generate new → Virtualenv
```

Recommended settings:

- Python 3.11 or 3.12
- Use a project-local `.venv`
- Do not inherit packages from the base interpreter
- Do not make the virtual environment available to all projects

Then open PyCharm Terminal and install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The PyCharm terminal should show `(.venv)` before the prompt.

## Usage

Taiwan Mandarin female voice:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female
```

Taiwan Mandarin male voice:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-male
```

U.S. English female voice:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice us-female
```

Another U.S. English female voice:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice us-female-2
```

U.S. English male voice:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice us-male
```

Raw Edge TTS voice name:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice en-US-AriaNeural
```

Custom output folder:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --output mp3_output
```

Slower speech:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --rate -10%
```

Slightly faster speech:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --rate +10%
```

Pitch adjustment:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --pitch +0Hz
```

Larger or smaller text chunks:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --max-chars 2500
```

Regenerate files even if MP3s already exist:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female --overwrite
```

If you installed the local CLI with `python -m pip install -e .`, replace `python epub_to_mp3.py` with `epub-to-mp3`:

```bash
epub-to-mp3 "books/your-book.epub" --voice tw-female
```

## Output

Example:

```bash
python epub_to_mp3.py "books/book.epub" --voice tw-female --output mp3_output
```

Output:

```text
mp3_output/
├── 001_001_Chapter_Title.mp3
├── 001_002_Chapter_Title.mp3
├── 002_001_Next_Chapter.mp3
└── ...
```

Each EPUB chapter may become multiple MP3 files because long chapters are split into smaller parts.

## Notes

This tool uses `edge-tts`, which requires internet access because speech generation is performed through Microsoft Edge's online TTS service.

This tool is intended for personal use with EPUB files you have the right to access. Do not use it to distribute copyrighted audiobooks without permission.

## Troubleshooting

### `ModuleNotFoundError`

Make sure your virtual environment is activated, then reinstall dependencies:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

In PyCharm, the terminal should usually show something like:

```text
(.venv) paulchiou@MacBookPro project-folder %
```

### `pip` installs globally instead of inside the project

Use `python -m pip` after activating the virtual environment:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Check which Python is being used:

```bash
which python
```

It should point to:

```text
.../project-folder/.venv/bin/python
```

### Weird install errors with Python 3.13

Use Python 3.11 or 3.12 for the project virtual environment.

### Voice sounds wrong

Try a different preset:

```bash
python epub_to_mp3.py "books/your-book.epub" --voice tw-female-2
```

or list all voices:

```bash
python epub_to_mp3.py --list-voices
```

## License

MIT License. See `LICENSE`.
