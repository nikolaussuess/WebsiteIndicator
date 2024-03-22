# WebsiteIndicator 
**a lightweight bookmark management app with (linux) system tray integration**

## Overview
*WebsiteIndicator* is a simple bookmark manager written in Python using Gtk3 for the user interface. It allows users to easily organize and access their favorite websites, documents, or any other resources. In addition, it integrates with the [Ayatana Application Indicator](https://github.com/AyatanaIndicators/libayatana-appindicator), providing a convenient way to access your bookmarks from the system tray.

## Features
* **System tray integration using an indicator**<br>
Access your bookmarks directly from the system tray using the Ayatana AppIndicator. The bookmarks can be organized in submenus.

* **Add and Edit Bookmarks**<br>
Easily add new bookmarks with custom names and URLs. Edit or delete existing bookmarks as needed (editing is not yet supported).

* **Search Functionality**<br>
Quickly search for specific bookmarks using the search window.

### Planned features
* Edit bookmarks
* Integration into firefox (via AddOn)
* Shell script support &ndash; add shell scripts to the menu
* Reordering of bookmarks using Drag and Drop

## Installation
### Dependencies
Before running WebsiteIndicator, make sure you have the following dependencies installed:

* Python 3.x (tested with Python 3.9)
* Gtk3 (and `python3-gi`)
* Ayatana AppIndicator (Debian package: `libayatana-appindicator3-1`)

### Run
You can just execute the program using
```bash
python3 main.py
```
This will start the indicator and will be the most important command. There are, however, some command line parameters. You may list them with:
```bash
python3 main.py --help
```

**Important:** Starting multiple instances of *WebsiteIndicator* that access the same file database may result in data loss!

## Configuration
The standard configuration can be customized via a config file called `config.yml`. The config file is either located in `$HOME/.config/WebsiteIndicator/` (preferred) or in the script directory (the same directory where the file `config.py` is located).

The capabilities are yet very limited (more options are planned in the future). The following parameters are supported:
```yaml
general:
  file_name: lesezeichen.xml # file name relative to config dir
  image_dir: ${CONFIG_DIR}/logos # the directory containing the icon images (${CONFIG_DIR} may be used and is replaced with the config directory, ${HOME} is replaced by the environment variable $HOME)
```

Note that some parameters (none of them listed above) are always overwritten and should not be set in the `config.yml`.

## Contributions
Contributions to WebsiteIndicator are welcome! Feel free to open issues, suggest improvements, or submit pull requests.