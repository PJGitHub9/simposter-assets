# simposter-assets

This repository contains studio logos used by [Simposter](https://github.com/PJGitHub9/Simposter/).

Thanks to [lynxstrike](https://github.com/lynxstrike) for sourcing the icons. We are not otherwise affiliated.

## Fonts

`fonts/` holds free fonts Simposter can download for poster text, so they don't depend on any other repo.

- `fonts/fonts.json` lists every font name Simposter can use (e.g. `Roboto-Medium`), the file it comes from, and, for variable fonts that hold several weights in one file, which named weight to use.
- `fonts/licenses/` has each family's license. All fonts here are under the SIL Open Font License 1.1 and come from [Google Fonts](https://github.com/google/fonts).

To add a font: put the `.ttf` in `fonts/`, its license in `fonts/licenses/`, and an entry per name in `fonts.json`. Only add fonts whose license allows redistribution (OFL or Apache 2.0); commercial fonts such as Arial or Helvetica can't go here.

## Starter overlays

`starter_overlays/` holds the ready-made overlays shown under **Overlays → Starter overlays** in Simposter. Simposter reads this folder when that window opens (at most every 10 minutes), so a new or updated starter only needs a push here, not a Simposter release.

- `starter_overlays/index.json` lists the files to read: `{"version": 1, "files": ["jmxd.json", ...]}`.
- Each file holds `{"version": 1, "overlays": [...]}`. Every overlay has an `id` (keep it the same across updates; that's how Simposter knows it's the same overlay), `name`, `description`, `notes`, `credit` (`author`, `url`), `conditions` (whole-overlay rules), `fonts` (`file`, `url`) and `elements` (the layers). Image layers use a `url` to the image, never an image file in this repo.
- Optional `min_version` (e.g. `"v1.8.40"`): older Simposter versions list the overlay but can't add it. Set it when a starter uses a newer overlay feature.

To add one: build it in Simposter, copy its layers into a new file here (image layers pointing at the creator's images with `url`), and add the file name to `index.json`. Users who already added a starter get the new version when they press **Replace**.

Images and fonts are not stored here and are not covered by this repository's license: they're downloaded from the creator's own repository when a user adds the overlay. Only link to files whose creator shares them publicly, and credit them in `notes` and `credit`. `jmxd.json` uses images and a font from [jmxd/Kometa](https://github.com/jmxd/Kometa), pinned to a commit.
