# Changelog

## [1.5.0] - 2026-02-14

### Added
- **XLIFF support** – Parse and translate `.xliff` and `.xlf` files (OASIS XLIFF 1.2)
- **Glossary** – New `--glossary` flag for custom term CSV files (source,target per line)
- **Progress bar** – Optional tqdm progress bar for large files (install `tqdm` to enable)
- **Test suite** – pytest-based tests for PO/TS/XLIFF parsing, placeholders, batch logic
- **GitHub Actions CI** – Lint (ruff) + test + automatic release on tag push

### Removed
- Removed i18n/gettext infrastructure and translated man pages (simplifies codebase)
- Removed old dist files from repository

### Changed
- Installation links in README updated to v1.5.0
- Build scripts cleaned up (no more locale packaging)

## [1.4.0] - 2026-02-05

### Added
- **Enhanced verbose mode** (`-V/--verbose`):
  - Per-batch timing with chars/second speed
  - Source/target character count tracking
  - Total API time vs total elapsed time
  - File parsing time
  - Average translation speed summary
- `translate_file()` now returns detailed stats (chars_source, chars_target, api_time)

## [1.3.4] - 2026-02-04

### Fixed
- Minor bug fixes

## [1.3.3] - 2026-02-04

### Added
- **Translated man pages**: Man pages now available in 44 languages
  - Section headers translated (NAME, DESCRIPTION, OPTIONS, etc.)
  - Installed to `/usr/share/man/<lang>/man1/`

## [1.3.2] - 2026-02-04

### Added
- **Man page**: `man po-translate` now available
  - Installed to `/usr/share/man/man1/po-translate.1.gz`

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
