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
   Run the `ResourcesCompile.bat` script located at the root of the plugin directory. This regenerates `resources3x.py` from `resources.qrc`:

   ```bat
   ResourcesCompile.bat
   ```

   > **Note:** The script uses the Python interpreter available on the system PATH. Make sure it is the Python bundled with QGIS (or that PyQt5 is installed in the active environment). If the compilation fails, set the `PATH` environment variable to point to the QGIS Python folder before running the script.

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

All three tools ship with **Qt5 Development Tools**. Install them for your platform:

| Platform | Command |
|---|---|
| **Windows** | Download OSGeo4W from https://trac.osgeo.org/osgeo4w/ and in Advanced mode install select qt5 and qt6 options (instead of Skip) |
| **macOS (Homebrew)** | `brew install qt@5` |
| **Ubuntu / Debian** | `sudo apt-get install qttools5-dev-tools qt5-qmake` |
| **Arch Linux** | `sudo pacman -S qt5-tools` |

### Step-by-step guide

#### 1. Generate / update the `.ts` template

Run `pylupdate5` against the project file to extract every translatable string from the source code and `.ui` files:

```bash
pylupdate5 qgisred.pro
```

This writes (or updates) `i18n/qgisred.ts`.

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

**Using Qt Linguist** (recommended for large files) whit OSGeo4W Shell:

```bash
# macOS (Homebrew)
/opt/homebrew/Cellar/qt@5/5.15.13_1/bin/linguist i18n/qgisred_es.ts

# Linux / Windows
"C:\Users\username\AppData\Local\Programs\OSGeo4W\apps\qt5\bin\linguist.exe" i18n/qgisred_es.ts
```

#### 4. Compile the translation

Once all strings are translated, compile the `.ts` file into a binary `.qm` file whit OSGeo4W Shell:

```bash
# macOS (Homebrew – adjust path to your Qt version)
/opt/homebrew/Cellar/qt@5/5.15.13_1/bin/lrelease i18n/qgisred_es.ts

# Linux / Windows
"C:\Users\username\AppData\Local\Programs\OSGeo4W\apps\qt5\bin\lrelease.exe" i18n/qgisred_es.ts
```

This produces `i18n/qgisred_es.qm`, which QGIS picks up automatically at startup.

#### 5. Test in QGIS

Set QGIS to the target language (*Settings → Options → General → User interface translation*), restart QGIS, and reload the plugin to verify the translations.

### Workflow summary

```
Install Qt5 tools → Update .ts template (pylupdate5) → Create/edit language file → Compile (lrelease) → Test in QGIS
```