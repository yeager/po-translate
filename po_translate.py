#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# po-translate - Batch translate .po and .ts files
# Copyright (C) 2026 Daniel Nylander <daniel@danielnylander.se>
"""
po-translate - Batch translate .po and .ts files using AI

Supports:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Lingva (free, no API key)
- Google Translate (free tier via googletrans)
"""

import argparse
import gettext
import json
import locale
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__version__ = "1.3.1"

# Translation setup
DOMAIN = "po-translate"

# Look for locale in multiple places
_possible_locale_dirs = [
    Path(__file__).parent / "locale",  # Development
    Path("/usr/share/po-translate/locale"),  # System install (Debian)
]
LOCALE_DIR = None
for _dir in _possible_locale_dirs:
    if _dir.exists():
        LOCALE_DIR = _dir
        break

# Initialize gettext - detect language
_system_lang = locale.getlocale()[0] or os.environ.get("LANG", "en")
_lang_code = _system_lang.split("_")[0].split(".")[0] if _system_lang else "en"

try:
    if LOCALE_DIR:
        translation = gettext.translation(DOMAIN, LOCALE_DIR, languages=[_lang_code], fallback=True)
    else:
        translation = gettext.NullTranslations()
    _ = translation.gettext
except Exception:
    def _(s): return s


@dataclass
class TranslationEntry:
    """A single translation entry."""
    msgid: str
    msgstr: str = ""
    msgctxt: str = ""
    comments: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    line: int = 0
    
    @property
    def needs_translation(self) -> bool:
        """Check if entry needs translation."""
        if not self.msgid:  # Header
            return False
        if self.msgstr:  # Already translated
            return False
        if 'fuzzy' in self.flags:  # Fuzzy = needs review, not retranslation
            return False
        return True


class POFile:
    """Parse and write .po files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.entries: list[TranslationEntry] = []
        self.header = ""
        self._parse()
    
    def _parse(self):
        """Parse PO file."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into blocks
        blocks = re.split(r'\n\n+', content)
        
        for block in blocks:
            if not block.strip():
                continue
            
            entry = self._parse_block(block)
            if entry:
                self.entries.append(entry)
    
    def _parse_block(self, block: str) -> Optional[TranslationEntry]:
        """Parse a single PO block."""
        lines = block.strip().split('\n')
        
        entry = TranslationEntry(msgid="", line=0)
        current_key = None
        
        for line in lines:
            line = line.strip()
            
            # Comments
            if line.startswith('#'):
                if line.startswith('#,'):
                    # Flags
                    flags = line[2:].strip().split(',')
                    entry.flags = [f.strip() for f in flags]
                else:
                    entry.comments.append(line)
                continue
            
            # msgctxt, msgid, msgstr
            for key in ['msgctxt', 'msgid', 'msgid_plural', 'msgstr']:
                if line.startswith(key):
                    match = re.match(rf'{key}(\[\d+\])?\s+"(.*)"', line)
                    if match:
                        suffix = match.group(1) or ''
                        value = self._unescape(match.group(2))
                        
                        if key == 'msgid':
                            entry.msgid = value
                        elif key == 'msgstr':
                            entry.msgstr = value
                        elif key == 'msgctxt':
                            entry.msgctxt = value
                        
                        current_key = key + suffix
                    break
            else:
                # Continuation line
                if line.startswith('"') and current_key:
                    match = re.match(r'"(.*)"', line)
                    if match:
                        value = self._unescape(match.group(1))
                        if current_key == 'msgid':
                            entry.msgid += value
                        elif current_key == 'msgstr':
                            entry.msgstr += value
                        elif current_key == 'msgctxt':
                            entry.msgctxt += value
        
        return entry if entry.msgid or entry.msgstr else None
    
    def _unescape(self, s: str) -> str:
        """Unescape PO string."""
        return s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    
    def _escape(self, s: str) -> str:
        """Escape string for PO file."""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
    
    def get_untranslated(self) -> list[TranslationEntry]:
        """Get entries that need translation."""
        return [e for e in self.entries if e.needs_translation]
    
    def save(self, filepath: str = None):
        """Save PO file."""
        filepath = filepath or self.filepath
        
        lines = []
        
        for entry in self.entries:
            # Comments
            for comment in entry.comments:
                lines.append(comment)
            
            # Flags
            if entry.flags:
                lines.append(f"#, {', '.join(entry.flags)}")
            
            # msgctxt
            if entry.msgctxt:
                lines.append(f'msgctxt "{self._escape(entry.msgctxt)}"')
            
            # msgid
            lines.append(f'msgid "{self._escape(entry.msgid)}"')
            
            # msgstr
            lines.append(f'msgstr "{self._escape(entry.msgstr)}"')
            
            lines.append('')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


class TSFile:
    """Parse and write Qt .ts files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.entries: list[TranslationEntry] = []
        self.root = None
        self._parse()
    
    def _parse(self):
        """Parse TS file."""
        import xml.etree.ElementTree as ET
        
        self.tree = ET.parse(self.filepath)
        self.root = self.tree.getroot()
        
        for context in self.root.findall('.//context'):
            context_name = context.findtext('name', '')
            
            for message in context.findall('message'):
                source = message.findtext('source', '')
                translation_elem = message.find('translation')
                
                translation = ''
                flags = []
                
                if translation_elem is not None:
                    translation = translation_elem.text or ''
                    if translation_elem.get('type') == 'unfinished':
                        flags.append('unfinished')
                
                entry = TranslationEntry(
                    msgid=source,
                    msgstr=translation,
                    msgctxt=context_name,
                    flags=flags
                )
                entry._message_elem = message  # Keep reference for saving
                self.entries.append(entry)
    
    def get_untranslated(self) -> list[TranslationEntry]:
        """Get entries that need translation."""
        return [e for e in self.entries if e.needs_translation or 'unfinished' in e.flags]
    
    def save(self, filepath: str = None):
        """Save TS file."""
        filepath = filepath or self.filepath
        
        for entry in self.entries:
            if hasattr(entry, '_message_elem'):
                translation_elem = entry._message_elem.find('translation')
                if translation_elem is not None:
                    translation_elem.text = entry.msgstr
                    if entry.msgstr:
                        # Remove 'unfinished' type when translated
                        if 'type' in translation_elem.attrib:
                            del translation_elem.attrib['type']
        
        self.tree.write(filepath, encoding='utf-8', xml_declaration=True)


class Translator:
    """Base translator class."""
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        raise NotImplementedError
    
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate multiple texts (default: one by one)."""
        results = []
        for text in texts:
            results.append(self.translate(text, source_lang, target_lang))
            time.sleep(0.1)  # Rate limiting
        return results


class LingvaTranslator(Translator):
    """Free translation via Lingva (Google Translate frontend)."""
    
    def __init__(self, url: str = "https://lingva.ml"):
        self.base_url = url.rstrip('/')
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return ""
        
        # Lingva API: /api/v1/{source}/{target}/{text}
        encoded_text = urllib.parse.quote(text)
        url = f"{self.base_url}/api/v1/{source_lang}/{target_lang}/{encoded_text}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'po-translate/1.0'})
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            data = json.loads(response.read().decode())
            return data.get('translation', text)
        except Exception as e:
            print(f"  ⚠️ Lingva error: {e}", file=sys.stderr)
            return text


class OpenAITranslator(Translator):
    """Translation via OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
    
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate batch using single API call."""
        if not texts:
            return []
        
        # Build prompt with numbered items
        items = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
        
        prompt = f"""Translate the following {len(texts)} UI strings from {source_lang} to {target_lang}.
Keep placeholders like {{0}}, %s, %d exactly as they are.
Keep it concise - these are UI labels.
Return ONLY the translations, one per line, numbered:

{items}"""
        
        url = f"{self.base_url}/chat/completions"
        
        data = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional translator for software localization. Translate accurately and concisely."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'po-translate/1.0'
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode())
            content = result['choices'][0]['message']['content']
            
            # Parse numbered responses
            translations = []
            for line in content.strip().split('\n'):
                # Remove numbering (1. 2. etc)
                match = re.match(r'^\d+\.\s*(.+)$', line.strip())
                if match:
                    translations.append(match.group(1))
            
            # Pad with originals if we didn't get enough
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
            
            return translations[:len(texts)]
            
        except Exception as e:
            print(f"  ⚠️ OpenAI error: {e}", file=sys.stderr)
            return texts
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else text


class AnthropicTranslator(Translator):
    """Translation via Anthropic API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
    
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate batch using single API call."""
        if not texts:
            return []
        
        items = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
        
        prompt = f"""Translate these {len(texts)} UI strings from {source_lang} to {target_lang}.
Keep placeholders like {{0}}, %s, %d exactly as they are.
Return ONLY the translations, one per line, numbered:

{items}"""
        
        url = "https://api.anthropic.com/v1/messages"
        
        data = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
                'User-Agent': 'po-translate/1.0'
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode())
            content = result['content'][0]['text']
            
            translations = []
            for line in content.strip().split('\n'):
                match = re.match(r'^\d+\.\s*(.+)$', line.strip())
                if match:
                    translations.append(match.group(1))
            
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
            
            return translations[:len(texts)]
            
        except Exception as e:
            print(f"  ⚠️ Anthropic error: {e}", file=sys.stderr)
            return texts
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else text


class MyMemoryTranslator(Translator):
    """Free translation via MyMemory API."""
    
    def __init__(self, email: str = None):
        self.email = email  # Optional, increases rate limit
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return ""
        
        params = {
            'q': text,
            'langpair': f'{source_lang}|{target_lang}'
        }
        if self.email:
            params['de'] = self.email
        
        url = f"https://api.mymemory.translated.net/get?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'po-translate/1.0'})
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            data = json.loads(response.read().decode())
            
            if data.get('responseStatus') == 200:
                return data['responseData']['translatedText']
            return text
            
        except Exception as e:
            print(f"  ⚠️ MyMemory error: {e}", file=sys.stderr)
            return text


class DeepLTranslator(Translator):
    """Translation via DeepL API (free or pro)."""
    
    def __init__(self, api_key: str, free: bool = False):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com" if free else "https://api.deepl.com"
    
    def _map_lang(self, lang: str) -> str:
        """Map language codes to DeepL format."""
        # DeepL uses uppercase and some specific codes
        lang_map = {
            'en': 'EN', 'de': 'DE', 'fr': 'FR', 'es': 'ES', 'it': 'IT',
            'nl': 'NL', 'pl': 'PL', 'pt': 'PT-PT', 'pt-br': 'PT-BR',
            'ru': 'RU', 'ja': 'JA', 'zh': 'ZH', 'ko': 'KO',
            'sv': 'SV', 'da': 'DA', 'fi': 'FI', 'nb': 'NB', 'no': 'NB',
            'el': 'EL', 'cs': 'CS', 'ro': 'RO', 'hu': 'HU', 'sk': 'SK',
            'sl': 'SL', 'bg': 'BG', 'et': 'ET', 'lv': 'LV', 'lt': 'LT',
            'uk': 'UK', 'id': 'ID', 'tr': 'TR',
        }
        return lang_map.get(lang.lower(), lang.upper())
    
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate batch using DeepL API."""
        if not texts:
            return []
        
        url = f"{self.base_url}/v2/translate"
        
        data = urllib.parse.urlencode({
            'auth_key': self.api_key,
            'text': texts,  # DeepL supports multiple texts
            'source_lang': self._map_lang(source_lang),
            'target_lang': self._map_lang(target_lang),
        }, doseq=True).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'po-translate/1.0'
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode())
            
            translations = [t['text'] for t in result.get('translations', [])]
            
            # Pad with originals if needed
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
            
            return translations[:len(texts)]
            
        except Exception as e:
            print(f"  ⚠️ DeepL error: {e}", file=sys.stderr)
            return texts
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else text


class LibreTranslateTranslator(Translator):
    """Translation via LibreTranslate API (self-hosted or public)."""
    
    def __init__(self, url: str = "https://libretranslate.com", api_key: str = None):
        self.base_url = url.rstrip('/')
        self.api_key = api_key
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return ""
        
        url = f"{self.base_url}/translate"
        
        payload = {
            'q': text,
            'source': source_lang,
            'target': target_lang,
            'format': 'text'
        }
        if self.api_key:
            payload['api_key'] = self.api_key
        
        data = json.dumps(payload).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'po-translate/1.0'
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode())
            return result.get('translatedText', text)
            
        except Exception as e:
            print(f"  ⚠️ LibreTranslate error: {e}", file=sys.stderr)
            return text


class GoogleCloudTranslator(Translator):
    """Translation via Google Cloud Translation API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate batch using Google Cloud API."""
        if not texts:
            return []
        
        url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
        
        data = json.dumps({
            'q': texts,
            'source': source_lang,
            'target': target_lang,
            'format': 'text'
        }).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'po-translate/1.0'
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode())
            
            translations = [t['translatedText'] for t in result['data']['translations']]
            
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
            
            return translations[:len(texts)]
            
        except Exception as e:
            print(f"  ⚠️ Google Cloud error: {e}", file=sys.stderr)
            return texts
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else text


def get_translator(service: str, config: dict) -> Translator:
    """Get translator instance for service."""
    if service == 'lingva':
        return LingvaTranslator(config.get('url') or 'https://lingva.ml')
    elif service == 'openai':
        if not config.get('api_key'):
            raise ValueError("OpenAI requires --api-key")
        return OpenAITranslator(
            config['api_key'],
            config.get('model', 'gpt-4o-mini'),
            config.get('base_url')
        )
    elif service == 'anthropic':
        if not config.get('api_key'):
            raise ValueError("Anthropic requires --api-key")
        return AnthropicTranslator(
            config['api_key'],
            config.get('model', 'claude-3-haiku-20240307')
        )
    elif service == 'mymemory':
        return MyMemoryTranslator(config.get('email'))
    elif service == 'deepl':
        if not config.get('api_key'):
            raise ValueError("DeepL requires --api-key")
        return DeepLTranslator(config['api_key'], free=False)
    elif service == 'deepl-free':
        if not config.get('api_key'):
            raise ValueError("DeepL Free requires --api-key")
        return DeepLTranslator(config['api_key'], free=True)
    elif service == 'libretranslate':
        return LibreTranslateTranslator(
            config.get('url', 'https://libretranslate.com'),
            config.get('api_key')
        )
    elif service == 'google':
        if not config.get('api_key'):
            raise ValueError("Google Cloud requires --api-key")
        return GoogleCloudTranslator(config['api_key'])
    else:
        raise ValueError(f"Unknown service: {service}")


def translate_file(filepath: str, translator: Translator, source_lang: str, target_lang: str, 
                   batch_size: int = 10, dry_run: bool = False) -> dict:
    """Translate a single file."""
    ext = Path(filepath).suffix.lower()
    
    # Parse file
    if ext == '.po':
        po_file = POFile(filepath)
    elif ext == '.ts':
        po_file = TSFile(filepath)
    else:
        return {'error': f'Unsupported format: {ext}'}
    
    # Get untranslated entries
    untranslated = po_file.get_untranslated()
    
    if not untranslated:
        return {'translated': 0, 'total': len(po_file.entries)}
    
    print(f"  📝 {len(untranslated)} strings to translate...")
    
    # Translate in batches
    translated_count = 0
    
    for i in range(0, len(untranslated), batch_size):
        batch = untranslated[i:i + batch_size]
        texts = [e.msgid for e in batch]
        
        print(f"  🔄 Batch {i//batch_size + 1}/{(len(untranslated) + batch_size - 1)//batch_size}...", end=' ', flush=True)
        
        translations = translator.translate_batch(texts, source_lang, target_lang)
        
        for entry, translation in zip(batch, translations):
            entry.msgstr = translation
            translated_count += 1
        
        print(f"✓")
        
        # Rate limiting between batches
        if i + batch_size < len(untranslated):
            time.sleep(0.5)
    
    # Save file
    if not dry_run:
        po_file.save()
        print(f"  💾 Saved: {filepath}")
    else:
        print(f"  🔍 Dry run: would save {filepath}")
    
    return {
        'translated': translated_count,
        'total': len(po_file.entries),
        'filepath': filepath
    }


def find_files(paths: list[str], recursive: bool = True) -> list[str]:
    """Find all .po and .ts files."""
    files = []
    
    for path in paths:
        path = Path(path)
        
        if path.is_file():
            if path.suffix.lower() in ('.po', '.ts'):
                files.append(str(path))
        elif path.is_dir():
            pattern = '**/*' if recursive else '*'
            for ext in ('.po', '.ts'):
                files.extend(str(f) for f in path.glob(f'{pattern}{ext}'))
    
    return files


def main():
    parser = argparse.ArgumentParser(
        description=_('po-translate - Batch translate .po and .ts files'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_("""
Examples:
  # Translate with free Lingva service
  po-translate --source en --target sv ./translations/
  
  # Translate with OpenAI
  po-translate --service openai --api-key sk-xxx --source en --target de ./po/
  
  # Dry run (don't save)
  po-translate --dry-run --source en --target fr messages.po
  
  # Translate single file
  po-translate --source en --target ja ./resources/strings.po

Services (free):
  lingva        Google Translate frontend (default)
  mymemory      1000 words/day free
  libretranslate  Self-hosted or public instances

Services (API key required):
  deepl         DeepL Pro (best for European languages)
  deepl-free    DeepL Free API
  google        Google Cloud Translation
  openai        GPT models (context-aware)
  anthropic     Claude models (context-aware)
        """)
    )
    
    parser.add_argument('paths', nargs='+', help=_('Files or directories to translate'))
    parser.add_argument('--source', '-s', required=True, help=_('Source language code (e.g., en)'))
    parser.add_argument('--target', '-t', help=_('Target language code (e.g., sv, de, fr). Defaults to system LANG.'))
    parser.add_argument('--service', default='lingva', 
                        choices=['lingva', 'mymemory', 'libretranslate', 'deepl', 'deepl-free', 'google', 'openai', 'anthropic'],
                        help=_('Translation service (default: lingva)'))
    parser.add_argument('--api-key', help=_('API key for paid services'))
    parser.add_argument('--url', help=_('Custom URL for LibreTranslate'))
    parser.add_argument('--model', help=_('Model for AI services (e.g., gpt-4o-mini, claude-3-haiku-20240307)'))
    parser.add_argument('--batch-size', type=int, default=10, help=_('Entries per API call (default: 10)'))
    parser.add_argument('--dry-run', action='store_true', help=_("Don't save changes"))
    parser.add_argument('--no-recursive', action='store_true', help=_("Don't search subdirectories"))
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Default target language from LANG environment variable
    if not args.target:
        lang_env = os.environ.get('LANG', os.environ.get('LC_ALL', ''))
        if lang_env:
            # Extract language code from LANG (e.g., "sv_SE.UTF-8" -> "sv")
            args.target = lang_env.split('_')[0].split('.')[0]
        if not args.target or args.target == 'C' or args.target == 'POSIX':
            print(_("❌ Error: --target required (could not detect from LANG environment)"), file=sys.stderr)
            sys.exit(1)
        print(_("ℹ️  Using target language from LANG: {lang}").format(lang=args.target))
    
    # Get translator
    config = {
        'api_key': args.api_key,
        'model': args.model,
        'url': args.url,
    }
    
    try:
        translator = get_translator(args.service, config)
    except ValueError as e:
        print(_("❌ Error: {error}").format(error=e), file=sys.stderr)
        sys.exit(1)
    
    # Find files
    files = find_files(args.paths, recursive=not args.no_recursive)
    
    if not files:
        print(_("❌ No .po or .ts files found"), file=sys.stderr)
        sys.exit(1)
    
    print(_("🌐 po-translate - {source} → {target}").format(source=args.source, target=args.target))
    print(_("📦 Service: {service}").format(service=args.service))
    print(_("📂 Files: {count}").format(count=len(files)))
    print()
    
    # Translate files
    total_translated = 0
    total_entries = 0
    
    for filepath in files:
        print(f"📄 {filepath}")
        
        try:
            result = translate_file(
                filepath,
                translator,
                args.source,
                args.target,
                batch_size=args.batch_size,
                dry_run=args.dry_run
            )
            
            if 'error' in result:
                print(_("  ❌ {error}").format(error=result['error']))
            else:
                total_translated += result['translated']
                total_entries += result['total']
                
        except Exception as e:
            print(_("  ❌ Error: {error}").format(error=e), file=sys.stderr)
        
        print()
    
    # Summary
    print("=" * 40)
    print(_("✅ Done! Translated {count} strings").format(count=total_translated))
    print(_("   Total entries: {count}").format(count=total_entries))
    
    if args.dry_run:
        print(_("   (dry run - no files modified)"))


if __name__ == '__main__':
    main()
