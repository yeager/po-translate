# po-translate

🌐 Batch translate `.po` and `.ts` localization files using AI or free services.

## Features

- **8 translation services** – Free and paid options
- **Batch translation** – Efficient API usage
- **Format support** – gettext `.po` and Qt `.ts` files
- **Preserves placeholders** – Keeps `{0}`, `%s`, `%d` intact
- **Dry run mode** – Preview changes before saving
- **LANG auto-detection** – Defaults target language from system locale

## Installation

### Debian/Ubuntu

```bash
wget https://github.com/yeager/po-translate/releases/download/v1.3.2/po-translate_1.3.2_all.deb
sudo dpkg -i po-translate_1.3.2_all.deb
```

### Fedora/RHEL/openSUSE

```bash
wget https://github.com/yeager/po-translate/releases/download/v1.3.2/po-translate-1.3.2-1.noarch.rpm
sudo rpm -i po-translate-1.3.2-1.noarch.rpm
```

### Arch Linux

```bash
wget https://github.com/yeager/po-translate/releases/download/v1.3.2/po-translate-1.3.2.pkg.tar.zst
sudo pacman -U po-translate-1.3.2.pkg.tar.zst
```

### Universal (tar.gz)

```bash
wget https://github.com/yeager/po-translate/releases/download/v1.3.2/po-translate-1.3.2.tar.gz
tar xzf po-translate-1.3.2.tar.gz -C /usr/local
```

### Windows/macOS (zip)

Download [po-translate-1.3.2.zip](https://github.com/yeager/po-translate/releases/download/v1.3.2/po-translate-1.3.2.zip), extract, and add to PATH.

### From source

```bash
git clone https://github.com/yeager/po-translate.git
cd po-translate
chmod +x po_translate.py
ln -s $(pwd)/po_translate.py /usr/local/bin/po-translate
```

## Usage

### Basic usage (free services)

```bash
# Translate with MyMemory (free, recommended)
po-translate --source en --target sv ./translations/

# Translate single file
po-translate --source en --target de messages.po

# Use LibreTranslate (self-hosted)
po-translate --service libretranslate --url http://localhost:5000 --source en --target fr ./po/
```

### With paid services (better quality)

```bash
# DeepL (best for European languages)
po-translate --service deepl --api-key xxx --source en --target de ./po/

# DeepL Free API
po-translate --service deepl-free --api-key xxx --source en --target sv ./po/

# Google Cloud Translation
po-translate --service google --api-key xxx --source en --target ja ./po/

# OpenAI (context-aware, best quality)
po-translate --service openai --api-key sk-xxx --source en --target ja ./po/

# Anthropic Claude
po-translate --service anthropic --api-key sk-ant-xxx --source en --target ko ./po/
```

### Options

| Option | Description |
|--------|-------------|
| `--source`, `-s` | Source language code (required) |
| `--target`, `-t` | Target language code (required) |
| `--service` | Translation service (default: lingva) |
| `--api-key` | API key for paid services |
| `--url` | Custom URL for LibreTranslate |
| `--model` | Model for AI services |
| `--batch-size` | Entries per API call (default: 10) |
| `--dry-run` | Preview without saving |
| `--no-recursive` | Don't search subdirectories |

## Services

### Free (no API key required)

| Service | Description | Limits |
|---------|-------------|--------|
| `lingva` | Google Translate frontend | Rate limited |
| `mymemory` | Translation memory | 1000 words/day |
| `libretranslate` | Self-hosted or public | Depends on instance |

### Paid (API key required)

| Service | Description | Pricing |
|---------|-------------|---------|
| `deepl` | DeepL Pro API | €5.49/month + usage |
| `deepl-free` | DeepL Free API | 500k chars/month |
| `google` | Google Cloud Translation | $20/million chars |
| `openai` | GPT models (context-aware) | ~$0.15/million tokens |
| `anthropic` | Claude models | ~$0.25/million tokens |

## Examples

### Translate all untranslated strings

```bash
po-translate --source en --target sv ./resources/language/
```

### Preview changes first

```bash
po-translate --dry-run --source en --target de ./translations/
```

### Use DeepL for high-quality European translations

```bash
po-translate --service deepl --api-key $DEEPL_API_KEY \
  --source en --target de ./po/
```

### Use GPT-4 for best quality (context-aware)

```bash
po-translate --service openai --api-key $OPENAI_API_KEY \
  --model gpt-4o --source en --target ja ./po/
```

## Language codes

Use ISO 639-1 codes:

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | ja | Japanese |
| sv | Swedish | zh | Chinese |
| de | German | ko | Korean |
| fr | French | ar | Arabic |
| es | Spanish | ru | Russian |
| it | Italian | pt | Portuguese |
| nl | Dutch | pl | Polish |

## Tips

1. **Start with dry-run** to preview translations
2. **Use DeepL** for European languages (best quality)
3. **Use AI services** for context-aware translations
4. **Increase batch-size** for AI services (more efficient)
5. **Review translations** – machine translation isn't perfect

## Related tools

- [l10n-lint](https://github.com/yeager/l10n-lint) – Lint your translation files

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

## License

GPL-3.0

## Author

**Daniel Nylander** ([@yeager](https://github.com/yeager))
