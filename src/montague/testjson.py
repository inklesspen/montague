from __future__ import absolute_import

import json


class JSONConfigLoader(object):
    """This is the simplest possible config loader. It assumes
       the JSON document is already in Montague Standard Format,
       and that no adjustments or error checking is required."""

    def __init__(self, path):
        self.path = path

    def config(self):
        return json.load(open(self.path))
