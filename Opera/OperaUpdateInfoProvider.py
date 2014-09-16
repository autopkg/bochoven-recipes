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


import urllib
import urllib2
import urlparse
import os
from xml.etree import ElementTree

from autopkglib import Processor, ProcessorError
from distutils.version import LooseVersion
from operator import itemgetter

__all__ = ["OperaUpdateInfoProvider"]

class OperaUpdateInfoProvider(Processor):
    description = "Provides URL to the highest version number or latest update."
    input_variables = {
        "update_url": {
            "required": True,
            "description": "URL for Opera update feed xml.",
        },
        "request_headers": {
            "required": True,
            "description": "Dictionary of additional HTTP headers to include in request.",
        }
    }
    output_variables = {
        "url": {
            "description": "URL for a download.",
        },
        "version": {
            "description": "Application version.",
        },
        "filename": {
            "description": "Filename for the zip file.",
        },
        "archive_format": {
            "description": "Zip archive.",
       }

    }

    __doc__ = description

    def get_feed_data(self, url):
        """Returns an array of dicts, with the primary and the fallback url:
            version: Version number
            tag: primary or fallback (not used yet)
            url: Url for the zip archive
        """
        

        # xml request that has to be sent to the opera update server
        xml_req = """<?xml version="1.0"?>
        <autoupdate schema-version="2.1" type="automatic">
            <system>
                <platform>
                    <opsys>MacOS</opsys>
                    <opsys-version>10.6.0</opsys-version>
                    <arch>i386</arch>
                    <package>ZIP</package>
                </platform>
            </system>
            <product>
                <name>Opera</name>
                <version>1.0</version>
                <language>en-US</language>
                <edition/>
            </product>
        </autoupdate>"""

        request = urllib2.Request(url, xml_req)

        # request header code borrowed from URLDownloader
        if "request_headers" in self.env:
            headers = self.env["request_headers"]
            for header, value in headers.items():
                request.add_header(header, value)

        try:
            url_handle = urllib2.urlopen(request)
        except:
            raise ProcessorError("Can't open URL %s" % request.get_full_url())

        print request.get_full_url()
        data = url_handle.read()

        try:
            xmldata = ElementTree.fromstring(data)
        except:
            raise ProcessorError("Error parsing XML from Opera Update feed.")

        items = xmldata.findall("product/files/file/download/")

        version = xmldata.find("product/files/file/version").text

        versions = []
        for item_elem in items:

            item = {}
            item["version"] = version
            item["tag"] = item_elem.tag
            item["url"] = item_elem.text

            versions.append(item)

        return versions

    def main(self):
        def compare_version(a, b):
            return cmp(LooseVersion(a), LooseVersion(b))

        items = self.get_feed_data(self.env.get("update_url"))
        sorted_items = sorted(items,
                              key=itemgetter("version"),
                              cmp=compare_version)
        latest = sorted_items[-1]
        self.output("Version retrieved from opera xml: %s" % latest["version"])

        self.env["VERSION"] = latest["version"]
        self.env["url"] = latest["url"]
        self.env["filename"] = "Opera-%s.zip" % latest["version"]
        self.output("Found URL %s" % self.env["url"])
        

if __name__ == "__main__":
    processor = OperaUpdateInfoProvider()
    processor.execute_shell()
