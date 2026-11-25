#!/usr/bin/env bash
# OuzFX – Kdenlive effects & transitions pack installer (Linux: native + Flatpak)
# https://github.com/AlfaPigeon/kdenlive-fx-pack
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK="$HERE/pack"
PROFILE="1080p"
TARGET="auto"
ACTION="install"
FLATPAK_ID="org.kde.kdenlive"

usage() {
  cat <<USAGE
Usage: ./install.sh [options]

  --profile 1080p|4k|vertical   project resolution the effect templates are built for (default: 1080p)
  --native                      install only for the distro / AppImage Kdenlive (~/.local/share/kdenlive)
  --flatpak                     install only for Flatpak Kdenlive (~/.var/app/$FLATPAK_ID/data/kdenlive)
  --both                        install for both
  --uninstall                   remove everything this pack installed
  --list                        show what would be installed
  -h, --help                    this help

Restart Kdenlive afterwards. Effects appear under Effects ▸ Templates (search "OuzFX"),
compositions under Compositions (search "OuzFX"), wipes in every Wipe/Luma list.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:?}"; shift 2 ;;
    --profile=*) PROFILE="${1#*=}"; shift ;;
    --native) TARGET="native"; shift ;;
    --flatpak) TARGET="flatpak"; shift ;;
    --both) TARGET="both"; shift ;;
    --uninstall|-u) ACTION="uninstall"; shift ;;
    --list) ACTION="list"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -d "$PACK/$PROFILE/effect-templates" ]] || { echo "Unknown profile '$PROFILE' (use 1080p, 4k or vertical)" >&2; exit 1; }

NATIVE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/kdenlive"
FLATPAK_DIR="$HOME/.var/app/$FLATPAK_ID/data/kdenlive"

detect_targets() {
  local t=()
  case "$TARGET" in
    native) t=("$NATIVE_DIR") ;;
    flatpak) t=("$FLATPAK_DIR") ;;
    both) t=("$NATIVE_DIR" "$FLATPAK_DIR") ;;
    auto)
      if command -v kdenlive >/dev/null 2>&1 || [[ -d "$NATIVE_DIR" ]]; then t+=("$NATIVE_DIR"); fi
      if { command -v flatpak >/dev/null 2>&1 && flatpak info "$FLATPAK_ID" >/dev/null 2>&1; } || [[ -d "$HOME/.var/app/$FLATPAK_ID" ]]; then
        t+=("$FLATPAK_DIR")
      fi
      [[ ${#t[@]} -eq 0 ]] && t=("$NATIVE_DIR")
      ;;
  esac
  printf '%s\n' "${t[@]}"
}

install_to() {
  local dest="$1" manifest
  manifest="$dest/ouzfx/manifest.txt"
  mkdir -p "$dest/effect-templates" "$dest/transitions" "$dest/lumas/HD/ouzfx" "$dest/lumas/VERTICAL/ouzfx" "$dest/ouzfx"
  : > "$manifest.new"
  for f in "$PACK/$PROFILE/effect-templates/"*.xml; do
    install -m 644 "$f" "$dest/effect-templates/"; echo "effect-templates/$(basename "$f")" >> "$manifest.new"
  done
  for f in "$PACK/$PROFILE/transitions/"*.xml; do
    sed "s#@LUMADIR@#$dest/lumas#g" "$f" > "$dest/transitions/$(basename "$f")"
    echo "transitions/$(basename "$f")" >> "$manifest.new"
  done
  for d in HD VERTICAL; do
    for f in "$PACK/lumas/$d/ouzfx/"*.png; do
      install -m 644 "$f" "$dest/lumas/$d/ouzfx/"; echo "lumas/$d/ouzfx/$(basename "$f")" >> "$manifest.new"
    done
  done
  if [[ -d "$HERE/overlays" ]]; then
    mkdir -p "$dest/ouzfx/overlays"
    cp -f "$HERE/overlays/"* "$dest/ouzfx/overlays/" 2>/dev/null || true
  fi
  echo "$PROFILE" > "$dest/ouzfx/profile"
  mv "$manifest.new" "$manifest"
  echo "✔ Installed $(grep -c . "$manifest") files into $dest  (profile: $PROFILE)"
}

uninstall_from() {
  local dest="$1" manifest="$1/ouzfx/manifest.txt"
  if [[ -f "$manifest" ]]; then
    while IFS= read -r rel; do rm -f "$dest/$rel"; done < "$manifest"
  fi
  # belt and braces: remove anything carrying our prefix
  rm -f "$dest"/effect-templates/ouzfx_*.xml "$dest"/transitions/ouzfx_*.xml
  rm -rf "$dest/lumas/HD/ouzfx" "$dest/lumas/VERTICAL/ouzfx" "$dest/ouzfx"
  echo "✔ Removed OuzFX from $dest"
}

mapfile -t DESTS < <(detect_targets)
case "$ACTION" in
  list)
    echo "Targets: ${DESTS[*]}"
    echo "Effect templates ($PROFILE): $(ls "$PACK/$PROFILE/effect-templates" | wc -l)"
    echo "Compositions ($PROFILE): $(ls "$PACK/$PROFILE/transitions" | wc -l)"
    echo "Luma wipes: $(ls "$PACK/lumas/HD/ouzfx" | wc -l) (HD) + $(ls "$PACK/lumas/VERTICAL/ouzfx" | wc -l) (vertical)"
    ;;
  install)
    for d in "${DESTS[@]}"; do install_to "$d"; done
    echo "Restart Kdenlive, then search \"OuzFX\" in the Effects and Compositions panels."
    ;;
  uninstall)
    for d in "${DESTS[@]}"; do uninstall_from "$d"; done
    ;;
esac
