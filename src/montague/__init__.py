from __future__ import absolute_import

from .loadwsgi import Loader

__version__ = "0.2.0"


def load_app(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_app(name)


def load_server(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_server(name)


def load_filter(config_path, name=None):
    loader = Loader(config_path)
    return loader.load_filter(name)


def load_logging_config(config_path, name=None):
    loader = Loader(config_path)
    return loader.logging_config(name)
