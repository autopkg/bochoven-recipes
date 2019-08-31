#!/usr/bin/env python
#
# Copyright 2014 Arjen van Bochoven
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import
from __future__ import print_function
import urllib
import urllib2
import urlparse
import os
import json

from autopkglib import Processor, ProcessorError

__all__ = ["OperaUpdateInfoProvider"]

class OperaUpdateInfoProvider(Processor):
    description = "Provides URL to the latest stable version."
    input_variables = {}
    output_variables = {
        "url": {
            "description": "URL for a download.",
        },
        "version": {
            "description": "Application version.",
        },
        "filename": {
            "description": "Filename for the zip file.",
        }
    }

    __doc__ = description

    def get_feed_data(self, url):
        """Returns a dict containing:
            version: latest
            url: Url for the zip archive
        """

        url = "https://autoupdate.geo.opera.com/netinstaller/Stable/MacOS"

        request = urllib2.Request(url)

        try:
            url_handle = urllib2.urlopen(request)
        except:
            raise ProcessorError("Can't open URL %s" % request.get_full_url())

        print(request.get_full_url())
        data = url_handle.read()

        # Todo, add a try catch block
        jsonData = json.loads(data)
        
        item = {}
        item["version"] = 'latest'
        item["filename"] = jsonData['installer_filename']
        item["url"] = jsonData['installer']

        return item

    def main(self):

        latest = self.get_feed_data(self.env.get("update_url"))

        self.output("Version retrieved from opera xml: %s" % latest["version"])

        self.env["VERSION"] = latest["version"]
        self.env["url"] = latest["url"]
        self.env["filename"] = latest["filename"]
        self.output("Found URL %s" % self.env["url"])
        

if __name__ == "__main__":
    processor = OperaUpdateInfoProvider()
    processor.execute_shell()
