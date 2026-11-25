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
FONTS=1

usage() {
  cat <<USAGE
Usage: ./install.sh [options]

  --profile 1080p|4k|vertical   project resolution the effect templates are built for (default: 1080p)
  --native                      install only for the distro / AppImage Kdenlive (~/.local/share/kdenlive)
  --flatpak                     install only for Flatpak Kdenlive (~/.var/app/$FLATPAK_ID/data/kdenlive)
  --both                        install for both
  --uninstall                   remove everything this pack installed
  --list                        show what would be installed
  --no-fonts                    don't install the free brand fonts to ~/.local/share/fonts/ouzfx
  -h, --help                    this help

Restart Kdenlive afterwards. Effects appear under Effects ▸ Templates (search "OuzFX" or
"AFX_"), audio presets under the audio effects' Templates, compositions under Compositions
(search "OuzFX"), wipes in every Wipe/Luma list, sound effects in the Library panel
(View ▸ Library ▸ OuzFX SFX) and in <data>/ouzfx/sfx, highlight overlays in the Library
panel (OuzFX Highlights) and in <data>/ouzfx/highlights, label title templates under
Project ▸ Add Template Title (ouzfx_*).
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
    --no-fonts) FONTS=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -d "$PACK/$PROFILE/effect-templates" ]] || { echo "Unknown profile '$PROFILE' (use 1080p, 4k or vertical)" >&2; exit 1; }

NATIVE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/kdenlive"
FONT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/ouzfx"
case "$PROFILE" in 4k) HL_SIZE=2160 ;; *) HL_SIZE=1080 ;; esac
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
    for f in "$HERE/overlays/"*; do
      install -m 644 "$f" "$dest/ouzfx/overlays/"; echo "ouzfx/overlays/$(basename "$f")" >> "$manifest.new"
    done
  fi
  # sound effects: <data>/ouzfx/sfx/<group>/*.wav, plus the same folder in Kdenlive's Library panel
  if [[ -d "$HERE/sfx" ]]; then
    for g in "$HERE/sfx/"*/; do
      g="$(basename "$g")"
      mkdir -p "$dest/ouzfx/sfx/$g" "$dest/library/OuzFX SFX/$g"
      for f in "$HERE/sfx/$g/"*.wav; do
        install -m 644 "$f" "$dest/ouzfx/sfx/$g/"; echo "ouzfx/sfx/$g/$(basename "$f")" >> "$manifest.new"
        install -m 644 "$f" "$dest/library/OuzFX SFX/$g/"; echo "library/OuzFX SFX/$g/$(basename "$f")" >> "$manifest.new"
      done
    done
  fi
  # highlight overlays (alpha WebM): <data>/ouzfx/highlights/<group>/ + Library ▸ OuzFX Highlights/<group>/
  if [[ -d "$HERE/highlights/$HL_SIZE" ]]; then
    rm -rf "$dest/ouzfx/highlights" "$dest/library/OuzFX Highlights"
    for g in "$HERE/highlights/$HL_SIZE/"*/; do
      g="$(basename "$g")"
      mkdir -p "$dest/ouzfx/highlights/$g" "$dest/library/OuzFX Highlights/$g"
      for f in "$HERE/highlights/$HL_SIZE/$g/"*.webm; do
        install -m 644 "$f" "$dest/ouzfx/highlights/$g/"; echo "ouzfx/highlights/$g/$(basename "$f")" >> "$manifest.new"
        install -m 644 "$f" "$dest/library/OuzFX Highlights/$g/"; echo "library/OuzFX Highlights/$g/$(basename "$f")" >> "$manifest.new"
      done
    done
  fi
  # editable label title templates: <data>/titles (Project ▸ Add Template Title) + <data>/ouzfx/titles
  if [[ -d "$HERE/titles/$PROFILE" ]]; then
    mkdir -p "$dest/titles" "$dest/ouzfx/titles"
    for f in "$HERE/titles/$PROFILE/"*.kdenlivetitle; do
      install -m 644 "$f" "$dest/titles/"; echo "titles/$(basename "$f")" >> "$manifest.new"
      install -m 644 "$f" "$dest/ouzfx/titles/"; echo "ouzfx/titles/$(basename "$f")" >> "$manifest.new"
    done
  fi
  echo "$PROFILE" > "$dest/ouzfx/profile"
  mv "$manifest.new" "$manifest"
  echo "✔ Installed $(grep -c . "$manifest") files into $dest  (profile: $PROFILE)"
  [[ -d "$dest/ouzfx/sfx" ]] && echo "  Sound effects: $dest/ouzfx/sfx  (also in Kdenlive's Library panel ▸ OuzFX SFX)"
  [[ -d "$dest/ouzfx/highlights" ]] && echo "  Highlights:    $dest/ouzfx/highlights  (Library panel ▸ OuzFX Highlights, ${HL_SIZE}px square)"
  [[ -d "$dest/ouzfx/titles" ]] && echo "  Label titles:  $dest/titles/ouzfx_*.kdenlivetitle  (Project ▸ Add Template Title)"
  return 0
}

install_fonts() {
  [[ "$FONTS" == 1 && -d "$HERE/fonts" ]] || return 0
  mkdir -p "$FONT_DIR"
  install -m 644 "$HERE/fonts/"*.ttf "$HERE/fonts/"OFL-*.txt "$FONT_DIR/"
  command -v fc-cache >/dev/null 2>&1 && fc-cache -f "$FONT_DIR" >/dev/null 2>&1 || true
  echo "✔ Brand fonts (Bricolage Grotesque, Plus Jakarta Sans, JetBrains Mono – OFL) in $FONT_DIR"
}

uninstall_from() {
  local dest="$1" manifest="$1/ouzfx/manifest.txt"
  if [[ -f "$manifest" ]]; then
    while IFS= read -r rel; do rm -f "$dest/$rel"; done < "$manifest"
  fi
  # belt and braces: remove anything carrying our prefix
  rm -f "$dest"/effect-templates/ouzfx_*.xml "$dest"/transitions/ouzfx_*.xml
  rm -rf "$dest/lumas/HD/ouzfx" "$dest/lumas/VERTICAL/ouzfx" "$dest/ouzfx" "$dest/library/OuzFX SFX" "$dest/library/OuzFX Highlights"
  rm -f "$dest"/titles/ouzfx_*.kdenlivetitle
  echo "✔ Removed OuzFX from $dest"
}

mapfile -t DESTS < <(detect_targets)
case "$ACTION" in
  list)
    echo "Targets: ${DESTS[*]}"
    ET="$PACK/$PROFILE/effect-templates"
    echo "Profile: $PROFILE"
    echo "Effect templates: $(ls "$ET" | wc -l)"
    echo "  v1.0 categories (Shake/Zoom/Anim/Screen 3D/Stylize/Look/Fast/Text): $(ls "$ET" | grep -vc '^ouzfx_afx_')"
    for c in move cam util style audio; do
      printf '  AFX_%-6s %3d\n' "${c^}" "$(ls "$ET" | grep -c "^ouzfx_afx_${c}_")"
    done
    echo "  Out / exit presets among the AFX ones: $(ls "$ET" | grep '^ouzfx_afx_' | grep -c '_out')"
    TR="$PACK/$PROFILE/transitions"
    echo "Compositions: $(ls "$TR" | wc -l)"
    echo "  v1.0: $(ls "$TR" | grep -vc '^ouzfx_afx_')   AFX: $(ls "$TR" | grep -c '^ouzfx_afx_') (whip push transitions: $(ls "$TR" | grep -c 'whip_push_out'), Out compositions: $(ls "$TR" | grep '^ouzfx_afx_' | grep -v whip_push | grep -c '_out'))"
    echo "Luma wipes: $(ls "$PACK/lumas/HD/ouzfx" | wc -l) (HD) + $(ls "$PACK/lumas/VERTICAL/ouzfx" | wc -l) (vertical)"
    [[ -d "$HERE/overlays" ]] && echo "Overlay clips: $(ls "$HERE/overlays" | wc -l)"
    if [[ -d "$HERE/sfx" ]]; then
      echo "Sound effects: $(find "$HERE/sfx" -name '*.wav' | wc -l)"
      for g in "$HERE/sfx/"*/; do printf '  %-9s %3d\n' "$(basename "$g")" "$(ls "$g"*.wav | wc -l)"; done
    fi
    if [[ -d "$HERE/highlights/$HL_SIZE" ]]; then
      echo "Highlight overlays (${HL_SIZE}px square alpha WebM): $(find "$HERE/highlights/$HL_SIZE" -name '*.webm' | wc -l)"
      for g in "$HERE/highlights/$HL_SIZE/"*/; do printf '  %-9s %3d\n' "$(basename "$g")" "$(ls "$g"*.webm | wc -l)"; done
    fi
    [[ -d "$HERE/titles/$PROFILE" ]] && echo "Label title templates: $(ls "$HERE/titles/$PROFILE/"*.kdenlivetitle | wc -l)"
    [[ -d "$HERE/fonts" && "$FONTS" == 1 ]] && echo "Brand fonts: $(ls "$HERE/fonts/"*.ttf | wc -l) -> $FONT_DIR"
    ;;
  install)
    for d in "${DESTS[@]}"; do install_to "$d"; done
    install_fonts
    echo "Restart Kdenlive, then search \"OuzFX\" (or \"AFX_\") in the Effects and Compositions panels."
    ;;
  uninstall)
    for d in "${DESTS[@]}"; do uninstall_from "$d"; done
    [[ -d "$FONT_DIR" ]] && rm -rf "$FONT_DIR" && { command -v fc-cache >/dev/null 2>&1 && fc-cache -f >/dev/null 2>&1 || true; } && echo "✔ Removed brand fonts from $FONT_DIR"
    ;;
esac
