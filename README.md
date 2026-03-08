# po-translate [![Version](https://img.shields.io/badge/version-1.5.7-blue.svg)](https://github.com/yeager/po-translate)

## Description

po-translate is a command-line tool for batch translating .po and .ts localization files using AI or free translation services. It supports multiple translation backends including free services like Lingva and MyMemory, as well as premium AI services like OpenAI GPT, Anthropic Claude, and DeepL.

The tool is designed for developers, translators, and localization teams who need to quickly translate large sets of localization files with consistency and accuracy. It includes features like custom glossaries, fuzzy marking, and dry-run capabilities.

## Features

- Multiple translation services (free and premium)
- Support for .po and .ts file formats
- Batch processing of multiple files
- Custom glossary support for consistent terminology
- AI services with context awareness
- Fuzzy marking for review workflows
- Dry-run mode for testing
- Recursive directory processing
- JSON output for automation

## Usage

### Basic Examples

```bash
# Translate with free Lingva service
po-translate --source en --target sv ./translations/

# Translate with OpenAI
po-translate --service openai --api-key sk-xxx --source en --target de ./po/

# Dry run (don't save)
po-translate --dry-run --source en --target fr messages.po

# Translate single file
po-translate --source en --target ja ./resources/strings.po

# Use custom glossary
po-translate --source en --target sv --glossary terms.csv ./po/
```

### Advanced Options

```bash
# Use DeepL with custom batch size
po-translate --service deepl --api-key your-key --batch-size 5 --source en --target de ./

# Mark translations as fuzzy for review
po-translate --fuzzy --source en --target sv ./po/

# Quiet mode with JSON output
po-translate --quiet --json --source en --target fr ./translations/
```

## Installation

### APT Repository (Debian/Ubuntu)

```bash
echo "deb https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager-l10n.list
sudo apt update
sudo apt install po-translate
```

### DNF Repository (Fedora/RHEL)

```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager-l10n.repo
sudo dnf install po-translate
```

### Building from Source

```bash
git clone https://github.com/yeager/po-translate.git
cd po-translate
pip install -e .
```

## Translation

This application is managed on Transifex: https://app.transifex.com/danielnylander/po-translate-ai/

Available in 11 languages: Swedish, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Czech, Russian, and Chinese (Simplified).

## License

GPL-3.0-or-later

## Author

Daniel Nylander (daniel@danielnylander.se)