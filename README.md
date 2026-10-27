# simposter-assets

This repository contains studio logos used by [Simposter](https://github.com/PJGitHub9/Simposter/).

Thanks to [lynxstrike](https://github.com/lynxstrike) for sourcing the icons. We are not otherwise affiliated.

## Fonts

`fonts/` holds free fonts Simposter can download for poster text, so they don't depend on any other repo.

- `fonts/fonts.json` lists every font name Simposter can use (e.g. `Roboto-Medium`), the file it comes from, and, for variable fonts that hold several weights in one file, which named weight to use.
- `fonts/licenses/` has each family's license. All fonts here are under the SIL Open Font License 1.1 and come from [Google Fonts](https://github.com/google/fonts).

To add a font: put the `.ttf` in `fonts/`, its license in `fonts/licenses/`, and an entry per name in `fonts.json`. Only add fonts whose license allows redistribution (OFL or Apache 2.0); commercial fonts such as Arial or Helvetica can't go here.
