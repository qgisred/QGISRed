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