#!/usr/bin/env python3
"""
EPUB TTS Converter

Convert EPUB files into chapter-by-chapter MP3 files using Microsoft Edge TTS.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

import ebooklib
import edge_tts
from bs4 import BeautifulSoup
from ebooklib import epub


VOICE_PRESETS = {
    "tw-female": "zh-TW-HsiaoChenNeural",
    "tw-female-2": "zh-TW-HsiaoYuNeural",
    "tw-male": "zh-TW-YunJheNeural",
    "us-female": "en-US-JennyNeural",
    "us-female-2": "en-US-AvaNeural",
    "us-male": "en-US-GuyNeural",
}

DEFAULT_VOICE = "tw-female"
DEFAULT_OUTPUT_DIR = "mp3_output"
DEFAULT_MAX_CHARS = 2500


class EpubTtsError(Exception):
    """Application-level error with a user-friendly message."""


def resolve_voice(voice: str) -> str:
    """Resolve a voice preset to a raw Edge TTS voice name."""
    return VOICE_PRESETS.get(voice, voice)


def safe_filename(name: str, fallback: str = "chapter") -> str:
    """Return a filesystem-safe filename component."""
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip(". ")
    return name[:90] or fallback


def normalize_text(text: str) -> str:
    """Clean extracted EPUB text while preserving paragraph breaks."""
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_sentence(sentence: str, max_chars: int) -> Iterable[str]:
    """Split a very long sentence by punctuation or hard character limits."""
    if len(sentence) <= max_chars:
        yield sentence
        return

    soft_parts = re.split(r"(?<=[，、,])", sentence)
    current = ""

    for part in soft_parts:
        part = part.strip()
        if not part:
            continue

        if len(current) + len(part) <= max_chars:
            current += part
        else:
            if current:
                yield current.strip()
            current = part

    if current.strip():
        long_part = current.strip()
        while len(long_part) > max_chars:
            yield long_part[:max_chars].strip()
            long_part = long_part[max_chars:]
        if long_part.strip():
            yield long_part.strip()


def split_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Split text into TTS-safe chunks, preferring sentence boundaries."""
    if max_chars < 500:
        raise EpubTtsError("--max-chars must be at least 500.")

    text = normalize_text(text)
    if not text:
        return []

    sentences = re.split(r"(?<=[。！？；.!?;\n])", text)
    chunks: list[str] = []
    current = ""

    for raw_sentence in sentences:
        sentence = raw_sentence.strip()
        if not sentence:
            continue

        sentence_parts = list(split_long_sentence(sentence, max_chars))
        for part in sentence_parts:
            if not current:
                current = part
            elif len(current) + 1 + len(part) <= max_chars:
                current += "\n" + part
            else:
                chunks.append(current.strip())
                current = part

    if current.strip():
        chunks.append(current.strip())

    return chunks


def extract_title(soup: BeautifulSoup, item_name: str, index: int) -> str:
    """Extract a reasonable chapter title from an EPUB XHTML document."""
    for selector in ["h1", "h2", "h3", "title"]:
        tag = soup.find(selector)
        if tag:
            title = tag.get_text(" ", strip=True)
            if title:
                return title

    path_title = Path(item_name).stem
    return path_title or f"chapter-{index:03d}"


def item_to_text(item: ebooklib.epub.EpubHtml, index: int) -> tuple[str, str]:
    """Convert one EPUB document item to title and cleaned text."""
    soup = BeautifulSoup(item.get_content(), "html.parser")

    for tag in soup(["script", "style", "nav"]):
        tag.decompose()

    title = extract_title(soup, item.get_name(), index)
    text = soup.get_text("\n")
    text = normalize_text(text)
    return title, text


def get_spine_document_items(book: epub.EpubBook) -> list[ebooklib.epub.EpubHtml]:
    """Return EPUB document items in reading/spine order when available."""
    items: list[ebooklib.epub.EpubHtml] = []
    seen_ids: set[str] = set()

    for spine_entry in book.spine:
        if isinstance(spine_entry, tuple):
            item_id = spine_entry[0]
        else:
            item_id = str(spine_entry)

        if item_id == "nav":
            continue

        item = book.get_item_with_id(item_id)
        if item is None:
            continue

        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items.append(item)
            seen_ids.add(item.get_id())

    # Fallback for EPUBs with incomplete spine metadata.
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT and item.get_id() not in seen_ids:
            items.append(item)

    return items


def extract_chapters(epub_path: Path, min_chars: int = 100) -> list[tuple[str, str]]:
    """Extract readable chapter/document text from an EPUB file."""
    if not epub_path.exists():
        raise EpubTtsError(f"EPUB file not found: {epub_path}")

    try:
        book = epub.read_epub(str(epub_path))
    except Exception as exc:  # noqa: BLE001
        raise EpubTtsError(f"Could not read EPUB file: {epub_path}\n{exc}") from exc

    chapters: list[tuple[str, str]] = []
    items = get_spine_document_items(book)

    for index, item in enumerate(items, start=1):
        title, text = item_to_text(item, index)
        if len(text) >= min_chars:
            chapters.append((title, text))

    if not chapters:
        raise EpubTtsError("No readable chapter text found in this EPUB.")

    return chapters


async def list_voices() -> None:
    """Print all available Edge TTS voices."""
    voices = await edge_tts.list_voices()
    for voice in voices:
        short_name = voice.get("ShortName", "")
        gender = voice.get("Gender", "")
        locale = voice.get("Locale", "")
        display_name = voice.get("FriendlyName", "")
        print(f"{short_name}\t{locale}\t{gender}\t{display_name}")


async def text_to_mp3(
    text: str,
    output_file: Path,
    voice: str,
    rate: str,
    volume: str,
    pitch: str,
) -> None:
    """Generate one MP3 file from text."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(str(output_file))


async def convert_epub_to_mp3(args: argparse.Namespace) -> None:
    epub_path = Path(args.epub_file).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    voice = resolve_voice(args.voice)

    output_dir.mkdir(parents=True, exist_ok=True)

    chapters = extract_chapters(epub_path, min_chars=args.min_chars)
    print(f"EPUB: {epub_path}")
    print(f"Voice: {voice} ({args.voice})")
    print(f"Output: {output_dir}")
    print(f"Found {len(chapters)} chapter/document sections.")

    for chapter_index, (title, text) in enumerate(chapters, start=1):
        chapter_name = safe_filename(title, fallback=f"chapter-{chapter_index:03d}")
        chunks = split_text(text, max_chars=args.max_chars)

        print(
            f"\n[{chapter_index:03d}/{len(chapters):03d}] "
            f"{chapter_name} — {len(chunks)} part(s)"
        )

        for part_index, chunk in enumerate(chunks, start=1):
            output_file = output_dir / f"{chapter_index:03d}_{part_index:03d}_{chapter_name}.mp3"

            if output_file.exists() and not args.overwrite:
                print(f"  Skipping existing: {output_file.name}")
                continue

            try:
                await text_to_mp3(
                    text=chunk,
                    output_file=output_file,
                    voice=voice,
                    rate=args.rate,
                    volume=args.volume,
                    pitch=args.pitch,
                )
            except Exception as exc:  # noqa: BLE001
                raise EpubTtsError(f"TTS failed for {output_file.name}: {exc}") from exc

            print(f"  Saved: {output_file.name}")

    print("\nDone.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an EPUB file into chapter-by-chapter MP3 audio using Edge TTS.",
    )
    parser.add_argument(
        "epub_file",
        nargs="?",
        help="Path to the EPUB file. Example: books/book.epub",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=(
            "Voice preset or raw Edge TTS voice name. "
            f"Default: {DEFAULT_VOICE}. Presets: {', '.join(VOICE_PRESETS.keys())}"
        ),
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        help="Speech rate, such as -10%%, +0%%, or +10%%. Default: +0%%",
    )
    parser.add_argument(
        "--volume",
        default="+0%",
        help="Speech volume, such as -10%%, +0%%, or +10%%. Default: +0%%",
    )
    parser.add_argument(
        "--pitch",
        default="+0Hz",
        help="Speech pitch, such as -10Hz, +0Hz, or +10Hz. Default: +0Hz",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Maximum characters per TTS chunk. Default: {DEFAULT_MAX_CHARS}",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=100,
        help="Minimum characters required to treat an EPUB document as a chapter. Default: 100",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate MP3 files even if they already exist.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available Edge TTS voices and exit.",
    )
    return parser


async def async_main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.list_voices:
            await list_voices()
            return 0

        if not args.epub_file:
            parser.error("epub_file is required unless --list-voices is used.")

        await convert_epub_to_mp3(args)
        return 0

    except EpubTtsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
