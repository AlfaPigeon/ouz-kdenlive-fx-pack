#!/usr/bin/env bash
# Build release assets into dist/ (GitHub Release + KDE Store uploads).
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${1:-$(cat VERSION)}"
rm -rf dist && mkdir -p dist/kde-store
NAME="kdenlive-fx-pack-v$VERSION"
STAGE="$(mktemp -d)/$NAME"
mkdir -p "$STAGE"
cp -r pack overlays sfx highlights titles fonts install.sh install.ps1 README.md CHANGELOG.md LICENSE VERSION "$STAGE/"
rm -f "$STAGE/sfx/sfx.json"
rm -f "$STAGE/pack/catalog.json" "$STAGE/titles/index.json"
mkdir -p "$STAGE/docs" && cp docs/BRAND.md "$STAGE/docs/"
( cd "$(dirname "$STAGE")" && tar czf "$OLDPWD/dist/$NAME.tar.gz" "$NAME" && python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1], \"zip\", \".\", sys.argv[2])" "$OLDPWD/dist/$NAME" "$NAME" )
# KDE Store / KNewStuff: files must sit at the archive ROOT, because Kdenlive's
# knsrc files extract archives straight into kdenlive/effect-templates and
# kdenlive/lumas/HD (non-recursive scan for effect templates).
for prof in 1080p 4k vertical; do
  tar czf "dist/kde-store/ouzfx-effect-templates-$prof-v$VERSION.tar.gz" -C "pack/$prof/effect-templates" .
done
tar czf "dist/kde-store/ouzfx-luma-wipes-hd-v$VERSION.tar.gz" -C pack/lumas/HD/ouzfx .
# Kdenlive "Download New Title Templates" (kdenlive_titles.knsrc) extracts into <data>/titles
for prof in 1080p 4k vertical; do
  tar czf "dist/kde-store/ouzfx-title-templates-$prof-v$VERSION.tar.gz" -C "titles/$prof" .
done
( cd dist && sha256sum *.tar.gz *.zip kde-store/* > SHA256SUMS )
ls -la dist dist/kde-store
