#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This file manages configurations and provides functionality to save and load them as well.
It also automatically triggers the saving of the configuration file whenever a setting is changed or deleted.
"""

import os
import json
from pathlib import Path


class ConfigDict(dict):
    """Set configs & save every time a setting changes"""
    __slots__ = ["path"]

    def __init__(self, config: dict, path: str):
        self.update(config)
        self.path = Path(path)

    def __setitem__(self, key, value):
        """Triggers whenever a value is set"""
        super().__setitem__(key, value)
        self.save()

    def __delitem__(self, key):
        """Triggers whenever a value is deleted"""
        super().__delitem__(key)
        self.save()

    def save(self):
        """Saves the config file to the given path"""
        with open(self.path, 'w') as file:
            json.dump(self, file, indent=2)

    def load(self):
        """Loads the config file from the given path"""
        with open(self.path, 'r') as file:
            self.update(json.load(file))


SETTINGS_PATH = 'settings.json'
config = ConfigDict({
    "_comments": {
        "source_path": "List of source paths (local folders) for backups (type: list with strings)",
        "destination_path": "Destination path (storage media) for backups (type: string)",
        "backup_to_cloud": "Flag indicating whether to backup to the cloud (specify: storage_provider) (type: boolean)",                    
        "notifications": "Enable or disable notifications (type: boolean)",
        "appearance_mode": "Appearance mode for the application (type: string)",
        "color_theme": "Color theme for the application (type: string)",
        "backup_expiry_date": "Expiry date for the backups in the storage media (type: string)",
        "storage_provider": "Storage provider for backups (Google Drive / FTP) (type: string)",
        "HOSTNAME": "Hostname for FTP configuration (type: string)",
        "USERNAME": "Username for FTP configuration (type: string)",
        "PASSWORD": "Password for FTP configuration (type: string)"
  },
    "source_path": [
        str(Path('~/Desktop').expanduser()).replace("\\", "/") + "/",
        str(Path('~/Documents').expanduser()).replace("\\", "/") + "/",
        str(Path('~/Downloads').expanduser()).replace("\\", "/") + "/",
    ],
    "destination_path": os.path.abspath(os.sep).replace("\\", "/"),
    "backup_to_cloud": False,
    "notifications": True,
    "appearance_mode": "dark",
    "color_theme": "blue",
    "backup_expiry_date": "Forever (default)",
    "storage_provider": "Google Drive",
    "HOSTNAME": "",
    "USERNAME": "",
    "PASSWORD": ""
}, SETTINGS_PATH)

if not os.path.exists(config.path):
    config.save()
