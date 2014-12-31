import os
from montague.ini import IniConfigLoader
from montague.loadwsgi import Loader
from montague import load_app, load_server, load_filter
from montague.structs import ComposedFilter, DEFAULT

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
            DEFAULT: {'use': 'package:FakeApp#basic_app'},
            'egg': {'use': 'egg:FakeApp#other'},
            'filtered-app': {
                'filter-with': 'filter',
                'use': 'package:FakeApp#basic_app'
            },
        },
        'filter': {
            'filter': {
                'method_to_call': 'lower',
                'use': 'egg:FakeApp#caps'
            },
            'filter1': {
                'filter-with': 'filter2',
                'use': 'egg:FakeApp#caps'
            },
            'filter2': {
                'use': 'egg:FakeApp#caps'
            },
        },
        'server': {
            'server_factory': {
                'port': '42',
                'use': 'egg:FakeApp#server_factory',
            },
            'server_runner': {
                'host': '127.0.0.1',
                'use': 'egg:FakeApp#server_runner'
            },
        },
    }
    assert config.config() == expected
    assert Loader(ini_path).config == expected


def test_load_app(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is fakeapp.apps.basic_app
    assert app2 is fakeapp.apps.basic_app2


def test_load_server(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    server = load_server(config_path, name='server_factory')
    actual = server(fakeapp.apps.basic_app)
    assert actual.montague_conf['local_conf']['port'] == '42'
    resp = actual.get('/')
    assert b'This is basic app' == resp.body
    server = load_server(config_path, name='server_runner')
    actual = server(fakeapp.apps.basic_app2)
    assert actual.montague_conf['local_conf']['host'] == '127.0.0.1'
    resp = actual.get('/')
    assert b'This is basic app2' == resp.body


def test_load_filter(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    filter = load_filter(config_path, name='filter')
    app = filter(None)
    assert isinstance(app, fakeapp.apps.CapFilter)


def test_load_filtered_app(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    app = load_app(config_path, name='filtered-app')
    assert isinstance(app, fakeapp.apps.CapFilter)
    assert app.app is fakeapp.apps.basic_app
    assert app.method_to_call == 'lower'


def test_load_layered_filter(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.ini')
    filter = load_filter(config_path, name='filter1')
    assert isinstance(filter, ComposedFilter)
    app = filter(fakeapp.apps.basic_app)
    assert app.app.app is fakeapp.apps.basic_app
    assert isinstance(app, fakeapp.apps.CapFilter)
    assert isinstance(app.app, fakeapp.apps.CapFilter)


def test_filter_app(fakeapp):
    # Specifically the 'filter-app' config type
    config_path = os.path.join(here, 'config_files/filter_app.ini')
    app = load_app(config_path)
    assert app.method_to_call == 'lower'
    assert app.app.method_to_call == 'upper'
    assert app.app.app is fakeapp.apps.basic_app
