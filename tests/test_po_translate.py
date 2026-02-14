"""Tests for po-translate."""
import os
import sys
import tempfile
import pytest

# Add parent dir so we can import po_translate
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import po_translate


# === PO Parsing ===

class TestPOFile:
    def _write_po(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.po', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return f.name

    def test_parse_basic(self):
        path = self._write_po('''\
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr ""

msgid "World"
msgstr "Mundo"
''')
        po = po_translate.POFile(path)
        assert len(po.entries) == 3  # header + 2
        os.unlink(path)

    def test_untranslated(self):
        path = self._write_po('''\
msgid ""
msgstr ""

msgid "Hello"
msgstr ""

msgid "Bye"
msgstr "Adiós"
''')
        po = po_translate.POFile(path)
        untranslated = po.get_untranslated()
        assert len(untranslated) == 1
        assert untranslated[0].msgid == "Hello"
        os.unlink(path)

    def test_fuzzy_skipped(self):
        path = self._write_po('''\
msgid ""
msgstr ""

#, fuzzy
msgid "Hello"
msgstr ""
''')
        po = po_translate.POFile(path)
        untranslated = po.get_untranslated()
        assert len(untranslated) == 0
        os.unlink(path)

    def test_msgctxt(self):
        path = self._write_po('''\
msgid ""
msgstr ""

msgctxt "menu"
msgid "File"
msgstr ""
''')
        po = po_translate.POFile(path)
        entries = [e for e in po.entries if e.msgid]
        assert entries[0].msgctxt == "menu"
        os.unlink(path)

    def test_save_roundtrip(self):
        path = self._write_po('''\
msgid ""
msgstr ""

msgid "Hello"
msgstr "Hej"
''')
        po = po_translate.POFile(path)
        po.save()
        po2 = po_translate.POFile(path)
        entries = [e for e in po2.entries if e.msgid]
        assert entries[0].msgstr == "Hej"
        os.unlink(path)

    def test_escape_unescape(self):
        path = self._write_po('''\
msgid ""
msgstr ""

msgid "Line1\\nLine2"
msgstr ""
''')
        po = po_translate.POFile(path)
        entries = [e for e in po.entries if e.msgid]
        assert "Line1\nLine2" == entries[0].msgid
        os.unlink(path)


# === TS Parsing ===

class TestTSFile:
    def _write_ts(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return f.name

    def test_parse_basic(self):
        path = self._write_ts('''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sv">
<context>
    <name>MainWindow</name>
    <message>
        <source>Hello</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Bye</source>
        <translation>Hejdå</translation>
    </message>
</context>
</TS>
''')
        ts = po_translate.TSFile(path)
        assert len(ts.entries) == 2
        os.unlink(path)

    def test_untranslated(self):
        path = self._write_ts('''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sv">
<context>
    <name>App</name>
    <message>
        <source>Open</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <source>Close</source>
        <translation>Stäng</translation>
    </message>
</context>
</TS>
''')
        ts = po_translate.TSFile(path)
        untranslated = ts.get_untranslated()
        assert len(untranslated) == 1
        assert untranslated[0].msgid == "Open"
        os.unlink(path)


# === Placeholder Preservation ===

class TestPlaceholders:
    """Test that placeholders are preserved in translations."""

    def test_printf_placeholders(self):
        """Verify placeholder regex patterns match common formats."""
        test_strings = [
            "Hello %s, you have %d items",
            "Progress: {0} of {1}",
            "File: %(filename)s",
            "Value: {value}",
        ]
        # Just verify these parse without error
        for s in test_strings:
            placeholders = po_translate.re.findall(r'%[sd]|%\([^)]+\)[sd]|\{[^}]*\}', s)
            assert len(placeholders) > 0

    def test_newline_preserved_in_po(self):
        """Ensure \\n in source matches in round-trip."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.po', delete=False, encoding='utf-8')
        f.write('msgid ""\nmsgstr ""\n\nmsgid "Line1\\nLine2"\nmsgstr "Rad1\\nRad2"\n')
        f.close()
        po = po_translate.POFile(f.name)
        po.save()
        po2 = po_translate.POFile(f.name)
        entry = [e for e in po2.entries if e.msgid][0]
        assert "\n" in entry.msgid
        assert "\n" in entry.msgstr
        os.unlink(f.name)


# === Batch Logic ===

class TestBatchTranslation:
    def test_batch_default(self):
        """Test that translate_batch calls translate for each item."""
        class DummyTranslator(po_translate.Translator):
            def translate(self, text, source_lang, target_lang):
                return f"[{target_lang}]{text}"

        t = DummyTranslator()
        results = t.translate_batch(["Hello", "World"], "en", "sv")
        assert results == ["[sv]Hello", "[sv]World"]

    def test_translate_file_no_untranslated(self):
        """translate_file returns 0 translated when all done."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.po', delete=False, encoding='utf-8')
        f.write('msgid ""\nmsgstr ""\n\nmsgid "Hi"\nmsgstr "Hej"\n')
        f.close()
        
        class Dummy(po_translate.Translator):
            def translate(self, text, sl, tl):
                return text

        result = po_translate.translate_file(f.name, Dummy(), "en", "sv", dry_run=True)
        assert result['translated'] == 0
        os.unlink(f.name)


# === XLIFF Parsing ===

class TestXLIFFFile:
    def _write_xliff(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.xliff', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return f.name

    def test_parse_xliff_v1(self):
        path = self._write_xliff('''\
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="sv" datatype="plaintext">
    <body>
      <trans-unit id="1">
        <source>Hello</source>
        <target></target>
      </trans-unit>
      <trans-unit id="2">
        <source>Bye</source>
        <target>Hejdå</target>
      </trans-unit>
    </body>
  </file>
</xliff>
''')
        xlf = po_translate.XLIFFFile(path)
        assert len(xlf.entries) == 2
        untranslated = xlf.get_untranslated()
        assert len(untranslated) == 1
        assert untranslated[0].msgid == "Hello"
        os.unlink(path)

    def test_save_xliff(self):
        path = self._write_xliff('''\
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="sv" datatype="plaintext">
    <body>
      <trans-unit id="1">
        <source>Hello</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>
''')
        xlf = po_translate.XLIFFFile(path)
        xlf.entries[0].msgstr = "Hej"
        xlf.save()
        xlf2 = po_translate.XLIFFFile(path)
        assert xlf2.entries[0].msgstr == "Hej"
        os.unlink(path)


# === Glossary ===

class TestGlossary:
    def test_load_glossary(self):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        f.write("source,target\nfile,fil\nopen,öppna\n")
        f.close()
        glossary = po_translate.load_glossary(f.name)
        assert glossary["file"] == "fil"
        assert glossary["open"] == "öppna"
        os.unlink(f.name)


# === find_files ===

class TestFindFiles:
    def test_find_po_files(self):
        with tempfile.TemporaryDirectory() as d:
            # Create test files
            open(os.path.join(d, "test.po"), 'w').close()
            open(os.path.join(d, "test.ts"), 'w').close()
            open(os.path.join(d, "test.txt"), 'w').close()
            files = po_translate.find_files([d])
            assert len(files) == 2

    def test_find_xliff_files(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "test.xliff"), 'w').close()
            open(os.path.join(d, "test.xlf"), 'w').close()
            files = po_translate.find_files([d])
            assert len(files) == 2
