#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This file allows you to sync your files with Google Drive.
It allows uploading, updating, and deleting files in a specified folder on Google Drive.
Note: This feature becomes optional in the program. If you want to use it, just turn the cloud switch on.
Follow instructions to get your Oauth2 credential key:
https://github.com/KafetzisThomas/SafeArchive/wiki/Obtaining-API-Key
"""

import os
import sys
import ftplib
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.settings import InvalidConfigError
from Scripts.notification_handlers import notify_client_secrets_file_missing
from Scripts.configs import config
config.load()  # Load the JSON file into memory


class GoogleDriveCloud:

    def initialize(self):
        """Authenticate request and initialize Google Drive"""

        try:
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            self.drive = GoogleDrive(gauth)
        except InvalidConfigError:
            notify_client_secrets_file_missing(config['notifications'])
            sys.exit()

        # Check if the folder already exists in Google Drive
        folder_query = ("title='SafeArchive' and mimeType='application/vnd.google-apps.folder' and trashed=false")
        file_list = self.drive.ListFile({'q': folder_query}).GetList()

        if file_list:
            # The folder already exists, so just update the existing files
            self.gdrive_folder = file_list[0]
        else:
            # The folder doesn't exist, so create a new one
            self.gdrive_folder = self.drive.CreateFile(
                {'title': 'SafeArchive', 'mimeType': 'application/vnd.google-apps.folder'})
            self.gdrive_folder.Upload()

    def get_cloud_usage_percentage(self):
        """Return cloud usage percentage"""
        account_details = self.drive.GetAbout()  # Get account details

        # Calculate storage usage percentage
        used_storage = int(account_details['quotaBytesUsed'])
        total_storage = int(account_details['quotaBytesTotal'])
        storage_usage_percentage = (used_storage / total_storage) * 100
        return storage_usage_percentage

    def get_or_create_folder(self, foldername, parent_folder_id=None):
        """Get or create folder in Google Drive"""
        folder_query = (f"title='{foldername}' and mimeType='application/vnd.google-apps.folder' and trashed=false")
        folder_list = self.drive.ListFile({'q': folder_query}).GetList()

        if folder_list:
            return folder_list[0]
        else:
            folder_metadata = {'title': foldername}
            if parent_folder_id:
                folder_metadata['parents'] = [{'id': parent_folder_id}]

            new_folder = self.drive.CreateFile(folder_metadata)
            new_folder.Upload()
            return new_folder

    def backup_to_google_drive(self, folderpath, DESTINATION_PATH, parent_folder_id=None):
        """Upload local backup files to Google Drive"""

        foldername = os.path.basename(folderpath)
        self.gdrive_folder = self.get_or_create_folder(foldername, parent_folder_id)

        for filename in os.listdir(folderpath):
            filepath = os.path.join(folderpath, filename)
            gdrive_file = self.get_or_create_file(filename, filepath)

            # Update existing files or upload new ones
            gdrive_file.SetContentFile(filepath)
            gdrive_file.Upload()

        # Delete files in Google Drive that don't exist in the local folder anymore
        self.delete_files_not_in_local_folder(DESTINATION_PATH[:-1])

    def get_or_create_file(self, filename, folderpath):
        """Get or create file in Google Drive"""

        file_query = (f"title='{filename}' and '{self.gdrive_folder['id']}' in parents and trashed=false")
        file_list = self.drive.ListFile({'q': file_query}).GetList()

        if file_list:
            return file_list[0]
        else:
            new_file = self.drive.CreateFile({'title': filename, 'parents': [{'id': self.gdrive_folder['id']}]})
            return new_file

    def delete_files_not_in_local_folder(self, local_folder_path):
        """Delete files in Google Drive that don't exist in the local folder"""
        drive_files = self.drive.ListFile({'q': f"'{self.gdrive_folder['id']}' in parents and trashed=false"}).GetList()

        for file in drive_files:
            local_file_path = os.path.join(local_folder_path, file['title'])
            if not os.path.exists(local_file_path):
                file.Trash()

class FTP:

    def __init__(self):
        """Initialize FTP server connection"""
        self.hostname = config['HOSTNAME']
        self.username = config['USERNAME']
        self.password = config['PASSWORD']
        self.ftp_server = None

    def connect(self):
        """Connect to FTP Server"""
        self.ftp_server = ftplib.FTP(self.hostname, self.username, self.password)
        self.ftp_server.encoding = "utf-8"  # force UTF-8 encoding

    def create_directory(self):
        """Create directory on FTP server"""
        try:
            self.ftp_server.mkd('/SafeArchive')
        except ftplib.error_perm:
            pass
        finally:
            self.ftp_server.cwd('/SafeArchive')

    def backup_to_ftp_server(self, folderpath):
        """Upload folder and its files to the FTP server"""
        self.connect()
        self.create_directory()

        for file in os.listdir(folderpath):
            file_path = os.path.join(folderpath, file)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    self.ftp_server.storbinary(f'STOR {file}', f)

        self.delete_files_not_in_local_folder(folderpath)
        self.disconnect()

    def delete_files_not_in_local_folder(self, folderpath):
        """Delete remote files that are not present locally"""
        remote_files = self.ftp_server.nlst()

        for file in remote_files:
            if file not in os.listdir(folderpath):
                self.ftp_server.delete(file)

    def disconnect(self):
        """Disconnect from FTP Server"""
        if self.ftp_server:
            self.ftp_server.quit()
