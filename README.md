# po-translate

🌐 Batch translate `.po` and `.ts` localization files using AI or free services.

## Features

- **Multiple services** – Free (Lingva, MyMemory) and paid (OpenAI, Anthropic)
- **Batch translation** – Efficient API usage with batched requests
- **Format support** – gettext `.po` and Qt `.ts` files
- **Preserves placeholders** – Keeps `{0}`, `%s`, `%d` intact
- **Dry run mode** – Preview changes before saving

## Installation

```bash
git clone https://github.com/yeager/po-translate.git
cd po-translate
chmod +x po_translate.py

# Optional: symlink to PATH
ln -s $(pwd)/po_translate.py /usr/local/bin/po-translate
```

## Usage

### Basic usage (free service)

```bash
# Translate with MyMemory (free, no API key)
po-translate --source en --target sv ./translations/

# Translate single file
po-translate --source en --target de messages.po
```

### With AI services (better quality)

```bash
# OpenAI (best quality)
po-translate --service openai --api-key sk-xxx --source en --target ja ./po/

# Anthropic Claude
po-translate --service anthropic --api-key sk-ant-xxx --source en --target fr ./po/
```

### Options

| Option | Description |
|--------|-------------|
| `--source`, `-s` | Source language code (required) |
| `--target`, `-t` | Target language code (required) |
| `--service` | Translation service (default: lingva) |
| `--api-key` | API key for paid services |
| `--model` | Model for AI services |
| `--batch-size` | Entries per API call (default: 10) |
| `--dry-run` | Preview without saving |
| `--no-recursive` | Don't search subdirectories |

## Services

### Free (no API key)

| Service | Pros | Cons |
|---------|------|------|
| `lingva` | Google Translate quality | Rate limited |
| `mymemory` | Good quality, 1000 words/day | Daily limit |

### Paid (API key required)

| Service | Pros | Cons |
|---------|------|------|
| `openai` | Best quality, context-aware | Cost per token |
| `anthropic` | Excellent quality | Cost per token |

## Examples

### Translate all Swedish files

```bash
po-translate --source en --target sv ./resources/language/resource.language.sv_se/
```

### Preview changes first

```bash
po-translate --dry-run --source en --target de ./translations/
```

### Use GPT-4 for best quality

```bash
po-translate --service openai --api-key $OPENAI_API_KEY \
  --model gpt-4o --source en --target ja ./po/
```

## Language codes

Use ISO 639-1 codes:

| Code | Language |
|------|----------|
| en | English |
| sv | Swedish |
| de | German |
| fr | French |
| es | Spanish |
| ja | Japanese |
| zh | Chinese |
| ko | Korean |
| ... | ... |

## Tips

1. **Start with dry-run** to preview translations
2. **Use AI services** for UI strings (context-aware)
3. **Increase batch-size** for AI services (more efficient)
4. **Review translations** – machine translation isn't perfect

## Related tools

- [l10n-lint](https://github.com/yeager/l10n-lint) – Lint your translation files

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

## License

GPL-3.0

## Author

**Daniel Nylander** ([@yeager](https://github.com/yeager))
