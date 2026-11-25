# Publishing OuzFX on the KDE Store (KNewStuff)

Kdenlive's built-in **Download New …** dialogs are KNewStuff clients for [store.kde.org](https://store.kde.org).
The relevant `.knsrc` files in Kdenlive's source (`data/knewstuff/`) are:

| Kdenlive dialog | KDE Store category | Installs into | Archive handling |
|---|---|---|---|
| Effects ▸ *Download New Effect Templates* | **Kdenlive Effect Templates** (cat. 686) | `<data>/kdenlive/effect-templates/` | `Uncompress=archive` |
| Wipe composition ▸ *Download* | **Kdenlive FX** | `<data>/kdenlive/lumas/HD/` | `Uncompress=archive` |

Kdenlive scans `effect-templates/` **non-recursively**, so every XML must sit at the **root** of the archive.
`tools/package.sh` builds archives that do exactly that:

```
dist/kde-store/ouzfx-effect-templates-1080p-v<VERSION>.tar.gz   -> Kdenlive Effect Templates
dist/kde-store/ouzfx-effect-templates-4k-v<VERSION>.tar.gz      -> Kdenlive Effect Templates (separate file on the same product)
dist/kde-store/ouzfx-effect-templates-vertical-v<VERSION>.tar.gz
dist/kde-store/ouzfx-luma-wipes-hd-v<VERSION>.tar.gz            -> Kdenlive FX (lumas)
```

## Upload steps

1. `python3 tools/build.py && python3 tools/validate.py && tools/package.sh`
2. Sign in at <https://store.kde.org> and choose **Add Product** (`/product/add`).
3. Product 1 – *OuzFX Effect Templates*: category **Kdenlive ▸ Kdenlive Effect Templates**. Upload the three
   `ouzfx-effect-templates-*.tar.gz` files (name each file after its resolution), add a GIF from `docs/previews/`
   as the gallery image, and link the GitHub repo.
4. Product 2 – *OuzFX Luma Wipes*: category **Kdenlive FX**, upload `ouzfx-luma-wipes-hd-*.tar.gz`.
5. Users can then install from inside Kdenlive (Effects ▸ Templates ▸ *Download New Effect Templates*, or the
   **Download** button next to the Wipe composition's luma picker). After installing, restart Kdenlive.

## What is *not* on the KDE Store

There is no KNewStuff category for **custom compositions** (`<data>/kdenlive/transitions/`) or for the overlay
clips, so those ship only through `install.sh` / `install.ps1` and the GitHub Release archive. The 5 OuzFX luma
*compositions* expect the wipes in `<data>/kdenlive/lumas/HD/ouzfx/` – the installer puts them there; the KDE Store
luma pack is still usable from the stock **Wipe** composition.
