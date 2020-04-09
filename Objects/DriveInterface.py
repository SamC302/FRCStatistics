from __future__ import print_function
import httplib2
import os
import time
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import tools
from oauth2client.service_account import ServiceAccountCredentials


class DriveInterface(object):
    def __init__(self, directory):
        try:
            import argparse

            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        self.folderID = '189q3moFP8-Dq9dHWCAgGjBvf5osC-2Km'
        self.files = os.listdir(directory)
        self.key = "C:/Users/samch/PycharmProjects/FRCStatistics/Credentials/our-audio-273419-1865397ccbc2.json"

        credentials = ServiceAccountCredentials.from_json_keyfile_name(filename=self.key,
                                                                       scopes='https://www.googleapis.com/auth/drive')
        service = discovery.build(serviceName="drive", version="v3", credentials=credentials)
        self.service = service

    def shareFolder(self, emailAddress):
        print("Sharing file with email: " + emailAddress)
        batch = self.new_batch_http_request(callback=self.callback)
        user_permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': emailAddress
        }
        batch.add(self.permissions().create(
            fileId=self.folderID,
            body=user_permission,
            fields='id',
        ))
        batch.execute()
        print("Sharing complete!\n")

    def callback(request_id, response, exception):
        if exception:
            # Handle error
            print(exception)
        else:
            print("Permission Id: %s" % response.get('id'))

    def uploadFilesToFolder(self):
        for file in self.files:
            file_metadata = {
                'name': file,
                'parents': [self.folderID]
            }
            media = MediaFileUpload('MatchData/Events/' + file, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
