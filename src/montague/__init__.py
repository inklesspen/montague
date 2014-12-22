from __future__ import absolute_import

__version__ = "0.1.0"

from .loadwsgi import Loader


def load_app(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_app(name)


def load_server(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_server(name)


def load_filter(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_filter(name)
