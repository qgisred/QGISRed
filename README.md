# QGISRed
## About

QGISRed is a freeware QGIS plugin developed to assist in building and analyzing hydraulic models of water distribution networks of any complexity, up to the level of detail required by Digital Twins. The plugin works seamlessly with QGIS which enables the user to georeference all network elements, use geographic background layers, edit graphical and alphanumeric data, use geoprocessing tools, visualize data by layers, customize the symbology, etc.

## Websites
Official: https://qgisred.upv.es
QGis repository: https://plugins.qgis.org/plugins/QGISRed/

## How to contribute
Read [Contributing](./CONTRIBUTING.md)

## Code of conduct
Read [Code of Conduct](./CODE_OF_CONDUCT.md)

## Adding images to the plugin

The plugin uses the Qt resource system to bundle images. All images are stored in the `images/` folder and registered in the `resources.qrc` file, which is then compiled into a Python module (`resources3x.py`) that QGIS loads at runtime.

### Step-by-step guide

1. **Add the image file**  
   Copy your image (`.png`, `.svg`, etc.) into the `images/` folder located at the root of the plugin directory.

2. **Register the image in `resources.qrc`**  
   Open `resources.qrc` and add a new `<file>` entry inside the `<qresource>` block, referencing your image with a path relative to the project root:

   ```xml
   <RCC>
       <qresource prefix="/">
           <!-- existing entries ... -->
           <file>images/myNewIcon.png</file>
       </qresource>
   </RCC>
   ```

3. **Compile the resources**  
   Run the `scripts\CompileImages.bat` script located in the `scripts/` folder. This regenerates `resources3x.py` from `resources.qrc`:

   ```bat
   scripts\CompileImages.bat
   ```

   > **Note:** The script uses the Python interpreter available on the system PATH. Make sure it is the Python bundled with QGIS (or that PyQt5 is installed in the active environment). If the compilation fails, set the `PATH` environment variable to point to the QGIS Python folder before running the script.
   >
   > **Note for QGIS 4.0:** The current system uses a compiled Python module (`resources3x.py`) to maintain dual compatibility (using a post-processing patch to replace `PyQt5` imports). However, when the plugin transitions to supporting only QGIS 4.0+, this management should be updated to use the native Qt6 `.rcc` binary format instead of the Python-compiled `.py` file.

4. **Use the image in your code**  
   Import the compiled resources module and reference the image via its Qt resource path:

   ```python
   import resources3x  # noqa – triggers resource registration

   icon = QIcon(":/images/myNewIcon.png")
   ```

   The prefix `:/` corresponds to the `prefix="/"` attribute defined in `resources.qrc`.

## Translating the plugin

QGISRed uses Qt's `.ts`/`.qm` translation system. Translation files live in the `i18n/` folder.

### Prerequisites

The following tools are required:

- **`pylupdate5`** – extracts translatable strings from source files into a `.ts` template.
- **`lrelease`** – compiles a `.ts` file into the binary `.qm` format that QGIS loads.
- **Qt Linguist** *(optional)* – GUI editor for `.ts` files.

All three tools ship with **Qt5 Development Tools**. Install them downloading OSGeo4W from https://trac.osgeo.org/osgeo4w/ and in the "Advanced mode" select qt5 and qt6 options (instead of Skip) in CommandLine and Desktop and qt5-devel, qt6-devel, python3-pyqt5 and python3-pyqt6 in libs. 

#### 1. Generate / update the `.ts` template

To automatically extract every translatable string from the source code and `.ui` files into a `.ts` template, simply run the `UpdateTranslations.bat` script located at the root of the plugin directory:

```bat
UpdateTranslations.bat
```

This script will seamlessly locate and open the OSGeo4W Shell and run `pylupdate5 qgisred.pro` in the background. This writes (or updates) the `.ts` files inside the `i18n/` folder.

#### 2. Create a new language file

Copy the template file and name the copy using the [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) language code:

```bash
cp i18n/qgisred.ts i18n/qgisred_<languageCode>.ts
# Example for French:
cp i18n/qgisred.ts i18n/qgisred_fr.ts
```

#### 3. Translate the strings

Open the `.ts` file with a text editor or with **Qt Linguist** and fill in the `<translation>` tags.

**Before:**
```xml
<message>
    <location filename="../ui/qgisred_thematicmaps_dialog.ui" line="20"/>
    <source>Thematic Maps</source>
    <translation type="unfinished"></translation>
</message>
```

**After:**
```xml
<message>
    <location filename="../ui/qgisred_thematicmaps_dialog.ui" line="20"/>
    <source>Thematic Maps</source>
    <translation>Mapas Temáticos</translation>
</message>
```

**Using Qt Linguist** (recommended for large files):

```bash
linguist i18n/qgisred_es.ts
```

#### 4. Compile the translation

Once all strings are translated, compile the `.ts` file into a binary `.qm` format that QGIS can read. You can easily do this by running the `CompileTranslations.bat` script located at the root of the plugin directory:

```bat
CompileTranslations.bat
```

This script will automatically open the OSGeo4W Shell and run `lrelease i18n/qgisred_es.ts` (and the other language defined in the scripts) in the plugin folder. This produces `i18n/qgisred_es.qm` (and the other language defined in the scripts), which QGIS picks up automatically at startup.

#### 5. Test in QGIS

Set QGIS to the target language (*Settings → Options → General → User interface translation*), restart QGIS, and reload the plugin to verify the translations.

### Workflow summary

```
Install Qt5 tools → Update .ts template (pylupdate5) → Create/edit language file → Compile (lrelease) → Test in QGIS
```

## Developer Setup

### Activating the pre-commit test hook

This repository ships a shared git hook that runs the test suite before every
commit. Each contributor must opt in once after cloning:

**Windows:**
```
scripts\setup-hooks.bat
```

What the script does: it runs `git config core.hooksPath .githooks`, which
tells git to look for hook scripts in the committed `.githooks/` directory
instead of the default `.git/hooks/` directory.

After setup, every `git commit` will automatically run
`python -m pytest tests/` and block the commit if any test fails.

To skip the hook in exceptional circumstances (not recommended):
```
git commit --no-verify
```

## Running Tests

The plugin uses **pytest** for automated testing.

### Prerequisites

You need `pytest` installed in your QGIS Python environment. To install it, open the terminal and run:

```bash
python -m pip install pytest
```

### How to run the tests

To run the entire test suite, execute the following command from the plugin root directory:

```bash
python -m pytest tests/ -v
```

If you are running from a standard Windows console and `python` does not point to the QGIS interpreter, use the full path:

```powershell
& "C:\Program Files\QGIS 3.44.1\apps\Python312\python.exe" -m pytest tests/ -v
```

All test logic and helpers are located in the `tests/` directory.

## Releasing a new version

The `scripts/` folder contains three scripts that automate the full release process:
update version numbers, generate the ZIP, and upload it to the FTP server.

### Scripts

| Script | Description |
|---|---|
| `scripts/release_beta.bat` | Double-click shortcut — proposes **patch+1** (e.g. `0.17.3 → 0.17.4`) |
| `scripts/release_official.bat` | Double-click shortcut — proposes **minor+1** (e.g. `0.17.3 → 0.18.0`) |
| `scripts/release.py` | Main Python script, called by the `.bat` wrappers |

### What it does

1. Reads the current version from `metadata.txt`.
2. Suggests the next version based on the release type (or asks for it manually).
3. You can accept the suggestion by pressing **Enter**, or type a different version.
4. Updates `metadata.txt` (`version=X.Y.Z`) and `qgisred.py` (`DependenciesVersion`).
5. Calls `MakeZip.bat` to generate `QGISRed_vX.Y.Z.zip` in the parent folder.
6. Uploads the ZIP to the FTP server.
7. Optionally deletes the local ZIP.

You can also invoke the script directly for full manual control:

```bat
python scripts\release.py              :: asks for version, no suggestion
python scripts\release.py --beta       :: suggests patch+1
python scripts\release.py --official   :: suggests minor+1
```

### FTP credentials

Credentials are stored in `scripts/.ftp_credentials` (never committed — already in `.gitignore`).
A template is provided in the repository at `scripts/.ftp_credentials.template`.

Fields:

| Field | Description |
|---|---|
| `host` | FTP server hostname |
| `port` | FTP port (default `21`) |
| `user` | FTP username |
| `password` | FTP password |
| `remote_dir` | Remote directory where the ZIP will be uploaded |
| `tls` | Set to `true` if the server requires FTPS (FTP over TLS) |

As an alternative to the file, you can set environment variables:
`FTP_HOST`, `FTP_PORT`, `FTP_USER`, `FTP_PASS`, `FTP_DIR`, `FTP_TLS`.

If the file does not exist and no environment variables are set, the script will ask
for the credentials interactively and offer to save them.

### First-time setup

1. Copy the template and rename it:
   ```bat
   copy scripts\.ftp_credentials.template scripts\.ftp_credentials
   ```
2. Open `scripts\.ftp_credentials` and fill in the real values.
3. Run `scripts\release_beta.bat` or `scripts\release_official.bat`.

## Publishing news / announcements

The plugin shows a news dialog on startup whenever the server publishes a new announcement.
The source files live in `news/` (git-ignored) and must be uploaded to the FTP server manually.

### Structure on the server

```
files/news/
  es/
    news.json       ← metadata in Spanish
    2026-04.html    ← HTML content in Spanish
  en/
    news.json       ← metadata in English
    2026-04.html    ← HTML content in English
```

### How to publish new news

1. **Archive the current news.**
   Copy the entire `news/es/` and `news/en/` folders into `news/old/<YYYY-MM-DD>/` before making any changes:
   ```
   news/old/es/2026-04-30/news.json
   news/old/es/2026-04-30/2026-04.html
   news/old/en/2026-04-30/news.json
   news/old/en/2026-04-30/2026-04.html
   ```

2. **Update the JSON files.**
   In both `news/es/news.json` and `news/en/news.json`, change the `id` field to a new unique string
   (e.g. `"2026-07-v0.19"`). This is what triggers the dialog on all users' machines — as long as
   the `id` differs from any ID stored in `%APPDATA%\QGISRed\seenNews.dat`, the dialog will appear.
   Update `title` and `html_url` accordingly.

3. **Update the HTML files.**
   Edit `news/es/<file>.html` and `news/en/<file>.html` with the new content.
   The `html_url` in each JSON is a relative path, so the HTML file must sit in the same folder as its JSON.

4. **Upload to the FTP server.**
   Replace the existing files on the server with the updated ones:
   - `files/news/es/news.json`
   - `files/news/es/<html_file>.html`
   - `files/news/en/news.json`
   - `files/news/en/<html_file>.html`


## Adding a new Section


The plugin logic is split into *Section* classes under `sections/`. Each Section is a plain Python class (no base class) that is mixed into the main `QGISRed` class via multiple inheritance. Adding a new section requires touching **5 files**:

### 1. `sections/your_section.py` — create the section

```python
# -*- coding: utf-8 -*-
"""Short description of what this section does."""

class YourSection:
    def someMethod(self):
        # self.tr() works normally — it resolves through LifecycleSection.tr()
        self.iface.messageBar().pushMessage(self.tr("Hello"))
```

### 2. `sections/__init__.py` — export the class

```python
from .your_section import YourSection

__all__ = [
    ...,
    "YourSection",
]
```

### 3. `qgisred.py` — add the class to the `QGISRed` hierarchy

```python
from .sections.your_section import YourSection

class QGISRed(
    LifecycleSection,
    ...,
    YourSection,   # add here
):
    ...
```

> **MRO note:** `LifecycleSection` must remain first so that `__init__`, `tr()`, and `initGui()` are resolved from there.

### 4. `sections/lifecycle_section.py` — register the context for translations

`tr()` searches a list of known section contexts. Append your class name to `_SECTION_CONTEXTS`:

```python
_SECTION_CONTEXTS = [
    "QGISRed",
    ...
    "YourSection",   # add here
]
```

Without this step, any `self.tr(...)` calls inside your section will not be translated.

### 5. `qgisred.pro` — register the file for `pylupdate5`

Add the new file to the `SOURCES` list so that `UpdateTranslations.bat` picks up its translatable strings:

```
SOURCES = ... \
          sections/your_section.py
```
