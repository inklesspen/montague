import os
import sys
import pytest
from montague.ini import IniConfigLoader
from montague.loadwsgi import Loader
from montague import load_app, load_server, load_filter, load_logging_config
from montague.structs import ComposedFilter
from montague.validation import validate_montague_standard_format, validate_config_loader_methods
import montague_testapps

here = os.path.dirname(__file__)


def test_read_config():
    ini_dir = os.path.join(here, 'config_files')
    ini_path = os.path.join(ini_dir, 'simple_config.ini')
    config = IniConfigLoader(ini_path)
    expected = {
        'globals': {
            'here': ini_dir,
            '__file__': ini_path,
            'foo': 'bar',
        },
        'application': {
            'main': {'use': 'package:montague_testapps#basic_app'},
            'egg': {'use': 'egg:montague_testapps#other'},
            'filtered-app': {
                'filter-with': 'filter',
                'use': 'package:montague_testapps#basic_app'
            },
        },
        'composite': {},
        'filter': {
            'filter': {
                'method_to_call': 'lower',
                'use': 'egg:montague_testapps#caps'
            },
            'filter1': {
                'filter-with': 'filter2',
                'use': 'egg:montague_testapps#caps'
            },
            'filter2': {
                'use': 'egg:montague_testapps#caps'
            },
        },
        'server': {
            'server_factory': {
                'port': '42',
                'use': 'egg:montague_testapps#server_factory',
            },
            'server_runner': {
                'host': '127.0.0.1',
                'use': 'egg:montague_testapps#server_runner'
            },
        },
        'logging': {
        },
    }
    assert config.config() == expected
    assert Loader(ini_path).config == expected


def test_load_app():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is montague_testapps.apps.basic_app
    assert app2 is montague_testapps.apps.basic_app2


def test_load_server():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    server = load_server(config_path, name='server_factory')
    actual = server(montague_testapps.apps.basic_app)
    assert actual.montague_conf['local_conf']['port'] == '42'
    resp = actual.get('/')
    assert b'This is basic app' == resp.body
    server = load_server(config_path, name='server_runner')
    actual = server(montague_testapps.apps.basic_app2)
    assert actual.montague_conf['local_conf']['host'] == '127.0.0.1'
    resp = actual.get('/')
    assert b'This is basic app2' == resp.body


def test_load_filter():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    filter = load_filter(config_path, name='filter')
    app = filter(None)
    assert isinstance(app, montague_testapps.apps.CapFilter)


def test_load_filtered_app():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    app = load_app(config_path, name='filtered-app')
    assert isinstance(app, montague_testapps.apps.CapFilter)
    assert app.app is montague_testapps.apps.basic_app
    assert app.method_to_call == 'lower'


def test_load_layered_filter():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    filter = load_filter(config_path, name='filter1')
    assert isinstance(filter, ComposedFilter)
    app = filter(montague_testapps.apps.basic_app)
    assert app.app.app is montague_testapps.apps.basic_app
    assert isinstance(app, montague_testapps.apps.CapFilter)
    assert isinstance(app.app, montague_testapps.apps.CapFilter)


def test_filter_app():
    # Specifically the 'filter-app' config type
    config_path = os.path.join(here, 'config_files/filter_app.ini')
    app = load_app(config_path)
    assert app.method_to_call == 'lower'
    assert app.app.method_to_call == 'upper'
    assert app.app.app is montague_testapps.apps.basic_app


def test_null_logging_config():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    loader = Loader(config_path)
    with pytest.raises(KeyError):
        loader.logging_config()


def test_logging_config():
    stream_key_name = 'stream' if (sys.version_info[0] > 2 or sys.version_info[1] > 6) else 'strm'
    expected = {
        'version': 1,
        'root': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'loggers': {
            'simpleExample': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'simple',
                stream_key_name: sys.stdout,
            },
            'syslog': {
                'class': 'logging.handlers.SysLogHandler',
                'level': 'WARNING',
                'formatter': 'complicated',
            }
        },
        'formatters': {
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'complicated': {
                'format': 'F1 %(asctime)s %(levelname)s %(message)s',
                'datefmt': '%a, %d %b %Y %H:%M:%S +0000',
            },
            'withclass': {
                '()': 'foobar.FooBarClass',
                'first': 'foo',
                'second': 'bar',
            },
        },
    }
    config_path = os.path.join(here, 'config_files/logging.ini')
    actual = load_logging_config(config_path)
    assert actual == expected


def test_validity():
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    config_loader = IniConfigLoader(config_path)
    validate_montague_standard_format(config_loader.config())
    validate_config_loader_methods(config_loader)
