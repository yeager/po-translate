# po-translate [![Version](https://img.shields.io/badge/version-1.6.1-blue.svg)](https://github.com/yeager/po-translate)

## Description

po-translate is a command-line tool for batch translating PO, Qt TS and XLIFF
localization files using AI or translation services. It supports multiple
backends including free services such as Lingva and MyMemory, as well as OpenAI,
Anthropic and DeepL.

The tool is designed for developers, translators, and localization teams who need to quickly translate large sets of localization files with consistency and accuracy. It includes features like custom glossaries, fuzzy marking, and dry-run capabilities.

## Features

- Multiple translation services (free and premium)
- Support for PO, Qt TS and XLIFF files
- Batch processing of multiple files
- Custom glossary support for consistent terminology
- AI services with context awareness
- Fuzzy marking for review workflows
- Dry-run mode for testing
- Recursive directory processing
- JSON output for automation
- Safe plural handling: every plural form is translated and preserved
- Placeholder validation and atomic writes: a failed or incomplete provider
  response never overwrites a catalog

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

### Direct DEB install (Debian/Ubuntu)

```bash
curl -LO https://yeager.github.io/debian-repo/pool/main/p/po-translate/po-translate_1.6.1_all.deb
sudo apt install ./po-translate_1.6.1_all.deb
```

The current package is available directly while the signed APT index awaits
the repository's existing signing key.

### DNF Repository (Fedora/RHEL)

```bash
sudo dnf config-manager addrepo --from-repofile=https://yeager.github.io/rpm-repo/yeager.repo
sudo dnf makecache
sudo dnf install po-translate
```

## Safe catalog updates

Plural translations are applied to their matching plural slots, including when
`--fuzzy` is used. Before writing, po-translate verifies placeholders and that
the provider supplied every required form. If a request fails, returns an empty
translation or changes placeholders, the input file is left unchanged. In
`--json` mode, results are written to standard output and diagnostics to
standard error for reliable automation.

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
