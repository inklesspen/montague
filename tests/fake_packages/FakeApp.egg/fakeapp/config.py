import json
from montague.interfaces import IConfigLoader, IConfigLoaderFactory
from zope.interface import directlyProvides, implementer


@implementer(IConfigLoader)
class JSONConfigLoader(object):
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path

    def config(self):
        return json.load(open(self.path))

    def app_config(self, name="main"):
        raise NotImplementedError

    def server_config(self, name="main"):
        raise NotImplementedError

    def filter_config(self, name="main"):
        raise NotImplementedError
