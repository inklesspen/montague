import json
import six
from montague.interfaces import IConfigLoader, IConfigLoaderFactory
from montague.structs import LoadableConfig, DEFAULT
from montague.vendor import reify
from zope.interface import directlyProvides, implementer


@implementer(IConfigLoader)
class JSONINIConfigLoader(object):
    """This is the simplest possible config loader; it uses the naming and
       structural conventions of standard ini files, simply providing JSON's
       types. Therefore, it need do nothing aside from implement ini_config()
       as simply parsing and returning the JSON data."""
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path

    def config(self):
        return json.load(open(self.path))

    def ini_config(self):
        return self.config()

    def app_config(self, name):
        raise NotImplementedError

    def server_config(self, name):
        raise NotImplementedError

    def filter_config(self, name):
        raise NotImplementedError


@implementer(IConfigLoader)
class JSONConfigLoader(object):
    """This is a more useful config loader. It uses a structural
       convention that makes more sense for JSON; the root object
       contains 'application' and 'server' keys, which each contain keys
       for the respective items. However, that means it must either
       provide ini_config() or [app|server|filter]_config(); I chose to
       do both."""
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path

    @reify
    def _config(self):
        return json.load(open(self.path))

    def config(self):
        return self._config

    def ini_config(self):
        retval = {}
        for name, config in six.iteritems(self._config['application']):
            retval[six.u('application:{0}'.format(name))] = config
        for name, config in six.iteritems(self._config['server']):
            retval[six.u('server:{0}'.format(name))] = config
        for name, config in six.iteritems(self._config['filter']):
            retval[six.u('filter:{0}'.format(name))] = config
        return retval

    def app_config(self, name):
        if name is DEFAULT:
            name = 'main'
        # Obviously this will throw a KeyError if the config isn't there.
        # A real implementation would have error handling here.
        config = self._config['application'][name]
        return LoadableConfig.app(name=name, config=config)

    def server_config(self, name):
        if name is DEFAULT:
            name = 'main'
        config = self._config['server'][name]
        return LoadableConfig.server(name=name, config=config)

    def filter_config(self, name):
        # Not covered in tests yet.
        raise NotImplementedError
