#!/usr/local/autopkg/python
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

import re

from autopkglib import ProcessorError, URLGetter

__all__ = ["OperaUpdateInfoProvider"]

DEFAULT_LISTING_URL = "https://get.geo.opera.com/pub/opera/desktop/"


class OperaUpdateInfoProvider(URLGetter):
    description = (
        "Provides the URL of the latest stable universal Opera Setup.dmg, "
        "found via the public release mirror."
    )
    input_variables = {
        "listing_url": {
            "required": False,
            "description": (
                "Directory listing of stable Opera releases. "
                "Default: %s" % DEFAULT_LISTING_URL
            ),
        },
        "update_url": {
            "required": False,
            "description": (
                "Deprecated and ignored. The autoupdate.geo.opera.com "
                "netinstaller feed no longer accepts GET requests."
            ),
        },
    }
    output_variables = {
        "url": {
            "description": "URL for a download.",
        },
        "version": {
            "description": "Application version.",
        },
        "filename": {
            "description": "Filename for the disk image.",
        },
    }

    __doc__ = description

    @staticmethod
    def version_key(version):
        return tuple(int(part) for part in version.split("."))

    def get_page(self, url):
        try:
            return self.download(url, text=True)
        except Exception as err:
            raise ProcessorError("Can't open URL %s: %s" % (url, err))

    def get_feed_data(self, listing_url):
        """Returns a dict containing:
            version: latest stable version that has a macOS build
            url: URL of the universal disk image
            filename: filename of the disk image
        """
        listing = self.get_page(listing_url)
        versions = sorted(
            set(re.findall(r'href="(\d+(?:\.\d+)+)/"', listing)),
            key=self.version_key,
            reverse=True,
        )
        if not versions:
            raise ProcessorError("No versions found at %s" % listing_url)

        # A version directory can exist before its macOS build is published,
        # so take the newest one that actually contains a Setup.dmg.
        for version in versions:
            filename = "Opera_%s_Setup.dmg" % version
            mac_url = "%s%s/mac/" % (listing_url, version)
            try:
                page = self.download(mac_url, text=True)
            except Exception:
                continue
            if filename in page:
                return {
                    "version": version,
                    "filename": filename,
                    "url": mac_url + filename,
                }

        raise ProcessorError("No macOS Setup.dmg found at %s" % listing_url)

    def main(self):
        listing_url = self.env.get("listing_url") or DEFAULT_LISTING_URL
        if not listing_url.endswith("/"):
            listing_url += "/"

        latest = self.get_feed_data(listing_url)

        self.env["version"] = latest["version"]
        self.env["url"] = latest["url"]
        self.env["filename"] = latest["filename"]
        self.output("Found version %s" % latest["version"])
        self.output("Found URL %s" % self.env["url"])


if __name__ == "__main__":
    processor = OperaUpdateInfoProvider()
    processor.execute_shell()
