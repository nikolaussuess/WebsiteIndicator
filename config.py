import os
import sys

import yaml

_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
_USER_CONFIG = os.path.join(os.getenv("HOME"), ".config")
_APP_NAME = "WebsiteIndicator"
_CONFIG_FILE = "config.yml"

if os.path.isdir(os.path.join(_USER_CONFIG, _APP_NAME)):
    _CONFIG_DIR = os.path.join(_USER_CONFIG, _APP_NAME)
else:
    _CONFIG_DIR = os.path.join(_SCRIPT_DIR)

if os.path.isfile(os.path.join(_CONFIG_DIR, _CONFIG_FILE)):
    with open(os.path.join(_CONFIG_DIR, _CONFIG_FILE), "r") as file:
        config = yaml.safe_load(file)
else:
    config = {}

config['dir'] = _CONFIG_DIR
config['script_dir'] = _SCRIPT_DIR

# Default value
if 'general' not in config:
    config['general'] = {}
if 'filter' not in config:
    config['filter'] = {}

if 'file_name' not in config['general']:
    config['general']['file_name'] = "lesezeichen.xml"
if 'image_dir' not in config['general']:
    config['general']['image_dir'] = os.path.join(_CONFIG_DIR, "logos")
else:
    config['general']['image_dir'] = config['general']['image_dir'].replace("${CONFIG_DIR}", _CONFIG_DIR)

config['general']['file_path'] = os.path.join(_CONFIG_DIR, config['general']['file_name'])

print("===== CONFIG =====")
yaml.dump(config, stream=sys.stdout)
print()