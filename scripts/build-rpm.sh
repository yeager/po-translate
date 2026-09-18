#!/bin/bash
set -euo pipefail

SRCDIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG="po-translate"
VER=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$SRCDIR/po_translate.py")

echo "Building ${PKG}-${VER} RPM locally..."

TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/${PKG}-${VER}"
cp "$SRCDIR/po_translate.py" "$SRCDIR/po-translate.1" "$TMPDIR/${PKG}-${VER}/"
cp "$SRCDIR/README.md" "$SRCDIR/CHANGELOG.md" "$SRCDIR/LICENSE" "$TMPDIR/${PKG}-${VER}/"
mkdir -p "$TMPDIR/${PKG}-${VER}/man"
gzip -9cn "$SRCDIR/po-translate.1" > "$TMPDIR/${PKG}-${VER}/man/po-translate.1.gz"
find "$TMPDIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
tar -czf "$TMPDIR/${PKG}-${VER}.tar.gz" -C "$TMPDIR" "${PKG}-${VER}"

RPMTOP="$TMPDIR/rpmbuild"
mkdir -p "$RPMTOP"/{SOURCES,SPECS,RPMS,BUILD,BUILDROOT,SRPMS}
cp "$TMPDIR/${PKG}-${VER}.tar.gz" "$RPMTOP/SOURCES/"
sed "s/^Version:[[:space:]]*.*/Version:        ${VER}/" \
  "$SRCDIR/scripts/${PKG}.spec" > "$RPMTOP/SPECS/${PKG}.spec"
rpmbuild -bb --define "_topdir $RPMTOP" "$RPMTOP/SPECS/${PKG}.spec"

mkdir -p "$SRCDIR/dist"
cp "$RPMTOP/RPMS/noarch/${PKG}-${VER}-1"*.noarch.rpm "$SRCDIR/dist/"

rm -rf "$TMPDIR"
echo "Built: $SRCDIR/dist/"
