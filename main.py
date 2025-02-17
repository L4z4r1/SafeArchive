#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Project Title: SafeArchive (https://github.com/KafetzisThomas/SafeArchive)
# Author / Project Owner: KafetzisThomas (https://github.com/KafetzisThomas)
# License: GPLv3
# NOTE: By contributing to this project, you agree to the terms of the GPLv3 license, and agree to grant the project owner the right to also provide or sell this software, including your contribution, to anyone under any other license, with no compensation to you.

version = "1.3.0"

# Import built-in modules
import os
import sys
import tkinter as tk

# Import module files
from Scripts.file_utils import get_backup_size
from Scripts.file_utils import storage_media_free_space
from Scripts.file_utils import last_backup
from Scripts.file_utils import update_listbox
from Scripts.file_utils import remove_item
from Scripts.file_utils import add_item
from Scripts.backup_utils import run_backup
from Scripts.restore import RestoreBackup
from Scripts.system_tray import hide_window
from Scripts.widgets import DrivesCombobox
from Scripts.widgets import CloudSwitch
from Scripts.widgets import BackupExpiryDateCombobox
from Scripts.notification_handlers import notify_drive_reconnection
from Scripts.settings import settings
from Scripts.configs import config
config.load() # Load the JSON file into memory

# Import other (third-party) modules
import humanize
import psutil
from PIL import Image
import customtkinter as ctk

# Get value from the JSON file
# Set the destination directory path (type: string)
DESTINATION_PATH = config['destination_path'] + 'SafeArchive/'


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        restore_backup = RestoreBackup(self, DESTINATION_PATH)
        ctk.set_appearance_mode(config['appearance_mode'])
        ctk.set_default_color_theme(config['color_theme'])

        if config['appearance_mode'] == "dark":
            background = "#343638"
            foreground = "white"
            image1 = "assets/restore.png"
            image2 = "assets/gear.png"
            fg_color = "#242424"
        else:
            background = "#ebebeb"
            foreground = "black"
            image1 = "assets/restore2.png"
            image2 = "assets/gear2.png"
            fg_color = "#ebebeb"

        def get_listbox_selection_background():
            if config['color_theme'] == "blue":
                return "#1f6aa5"
            else:
                return "#2fa572"

        self.title(f"SafeArchive {version}")  # Set window title
        self.resizable(False, False)  # Disable minimize/maximize buttons
        self.geometry("500x500")  # Set window size
        self.iconbitmap("assets/icon.ico")  # Set window title icon

        try:
            # Create the destination directory path if it doesn't exist
            if not os.path.exists(DESTINATION_PATH):
                os.makedirs(DESTINATION_PATH)
        except FileNotFoundError:
            notify_drive_reconnection(config['notifications'])
            sys.exit()
        except PermissionError:
            print(f"No permissions given to make directory: '{DESTINATION_PATH}'.",
                  "Change it in settings.json or run with elevated priveleges")
            sys.exit(77)

        backup_options_label = ctk.CTkLabel(
            master=self, text="Drive Properties ━━━━━━━━━━━━━━━━", font=('Helvetica', 20))
        backup_options_label.place(x=15, y=15)

        device_label = ctk.CTkLabel(
            master=self, text="Device", font=('Helvetica', 12))
        device_label.place(x=15, y=45)

        drives = psutil.disk_partitions()
        drive_options = [drive.device.replace('\\', '/') for drive in drives]

        device_combobox_var = ctk.StringVar(
            value=DESTINATION_PATH.replace('SafeArchive/', ''))  # Set initial value

        drives_combobox = ctk.CTkComboBox(
            master=self, width=470, values=drive_options, command=DrivesCombobox, variable=device_combobox_var)
        drives_combobox.place(x=15, y=70)

        size_of_backup_label = ctk.CTkLabel(
            master=self, text=f"Size of backup: {humanize.naturalsize(get_backup_size(DESTINATION_PATH))}", font=('Helvetica', 12))
        size_of_backup_label.place(x=15, y=100)

        total_drive_space_label = ctk.CTkLabel(
            master=self, text=f"Free space on ({DESTINATION_PATH.replace('SafeArchive/', '')}): {storage_media_free_space()} GB", font=('Helvetica', 12))
        total_drive_space_label.place(x=15, y=120)

        last_backup_label = ctk.CTkLabel(
            master=self, text=f"Last backup: {last_backup(DESTINATION_PATH)}", font=('Helvetica', 12))
        last_backup_label.place(x=15, y=140)

        additional_settings_label = ctk.CTkLabel(
            master=self, text="Backup Options ━━━━━━━━━━━━━━━━", font=('Helvetica', 20))
        additional_settings_label.place(x=15, y=170)

        keep_my_backups_label = ctk.CTkLabel(
            master=self, text="Keep my backups", font=('Helvetica', 12))
        keep_my_backups_label.place(x=15, y=200)

        backup_expiry_date_combobox_var = ctk.StringVar(
            value=config['backup_expiry_date'])  # Set initial value
        backup_expiry_date_options = [
            "1 month", "3 months", "6 months", "9 months", "1 year", "Forever (default)"]

        backup_expiry_date_combobox = ctk.CTkComboBox(
            master=self,
            width=150,
            values=backup_expiry_date_options,
            command=BackupExpiryDateCombobox,
            variable=backup_expiry_date_combobox_var
        )

        backup_expiry_date_combobox.place(x=15, y=225)

        cloud_switch_var = ctk.StringVar(
            value="on" if config['backup_to_cloud'] else "off")  # Set initial value

        switch = ctk.CTkSwitch(
            master=self,
            text="Back up to Cloud",
            command=lambda: CloudSwitch(cloud_switch_var),
            variable=cloud_switch_var,
            onvalue="on",
            offvalue="off"
        )

        switch.place(x=340, y=225)

        backup_these_folders_label = ctk.CTkLabel(
            master=self, text="Backup these folders", font=('Helvetica', 12))
        backup_these_folders_label.place(x=15, y=255)

        frame = ctk.CTkFrame(master=self, corner_radius=10)
        frame.place(x=10, y=280)

        listbox = tk.Listbox(
            master=frame,
            height=4,
            width=52,
            background=background,
            foreground=foreground,
            activestyle='dotbox',
            font='Helvetica',
            selectbackground=get_listbox_selection_background()
        )

        listbox.pack(padx=7, pady=7)
        update_listbox(listbox)

        plus_button = ctk.CTkButton(
            master=self, text="+", width=20, height=10, command=lambda: add_item(listbox))
        plus_button.place(x=220, y=250)

        minus_button = ctk.CTkButton(
            master=self, text="-", width=20, height=10, command=lambda: remove_item(listbox))
        minus_button.place(x=250, y=250)

        status_label = ctk.CTkLabel(
            master=self, text="Status ━━━━━━━━━━━━━━━━━━━━", font=('Helvetica', 20))
        status_label.place(x=15, y=375)

        self.backup_progressbar = ctk.CTkProgressBar(
            master=self, width=475, height=15, corner_radius=0, orientation='horizontal', mode='indeterminate')
        self.backup_progressbar.place(x=15, y=415)

        restore_image = ctk.CTkImage(Image.open(image1), size=(25, 25))
        self.restore_button = ctk.CTkButton(master=self, text="", fg_color=fg_color, image=restore_image,
                                            width=5, height=5, command=lambda: restore_backup.restore_backup())
        self.restore_button.place(x=50, y=450)

        settings_image = ctk.CTkImage(Image.open(image2), size=(25, 25))
        self.settings_button = ctk.CTkButton(master=self, text="", fg_color=fg_color, image=settings_image,
                                             width=5, height=5, command=lambda: settings(App=self))
        self.settings_button.place(x=15, y=450)

        self.backup_button = ctk.CTkButton(master=self, text="BACKUP", command=lambda: run_backup(
            DESTINATION_PATH=DESTINATION_PATH, App=self))
        self.backup_button.place(x=200, y=450)

        close_button = ctk.CTkButton(
            master=self, text="CLOSE", command=self.destroy)
        close_button.place(x=350, y=450)

        self.protocol('WM_DELETE_WINDOW', lambda: hide_window(
            DESTINATION_PATH=DESTINATION_PATH, App=self))


if __name__ == "__main__":
    app = App()
    app.mainloop()
