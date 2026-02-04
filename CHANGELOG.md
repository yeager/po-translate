# Changelog

## [1.3.1] - 2026-02-04

### Changed
- **Debian policy compliance**: Packages now follow Debian packaging guidelines
  - Locale files installed to `/usr/share/po-translate/locale/`
  - Added `/usr/share/doc/po-translate/copyright`
  - Fixed locale lookup path in script

## [1.3.0] - 2026-02-04

### Added
- **LANG auto-detection**: `--target` now defaults to system LANG environment variable
  - Reads from `LANG` or `LC_ALL` environment variables
  - Extracts language code (e.g., `sv_SE.UTF-8` → `sv`)
  - Falls back to error if LANG not set or is `C`/`POSIX`

### Changed
- `--target` is no longer required if LANG is set

## [1.2.0] - 2026-02-03

### Added
- Localized output in 45+ languages
- Translations for: Arabic, Bulgarian, Czech, Danish, German, Greek, Spanish, Finnish, French, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Dutch, Norwegian, Polish, Portuguese, Romanian, Russian, Swedish, Thai, Turkish, Ukrainian, Vietnamese, Chinese

### Fixed
- Debian package architecture (now `all` instead of `arm64`)

## [1.1.0] - 2026-02-03

### Added
- DeepL Free API support (`deepl-free` service)
- Better error messages

## [1.0.0] - 2026-02-03

### Added
- Initial release
- Support for 8 translation services: Lingva, MyMemory, LibreTranslate, DeepL, Google, OpenAI, Anthropic
- Batch translation of .po and .ts files
- Fuzzy translation handling
