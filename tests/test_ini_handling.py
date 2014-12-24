import os
from montague.ini import IniConfigLoader
from montague.loadwsgi import Loader
from montague import load_app, load_server, load_filter
from montague.structs import ComposedFilter

here = os.path.dirname(__file__)


def test_read_config():
    ini_path = os.path.join(here, 'config_files/simple_config.ini')
    config = IniConfigLoader(ini_path)
    expected = {
        'application:main': {'use': 'package:FakeApp#basic_app'},
        'application:egg': {'use': 'egg:FakeApp#other'},
        'server:server_factory': {
            'port': '42',
            'use': 'egg:FakeApp#server_factory',
        },
        'server:server_runner': {
            'host': '127.0.0.1',
            'use': 'egg:FakeApp#server_runner'
        },
        'filter:filter': {
            'method_to_call': 'lower',
            'use': 'egg:FakeApp#caps'
        },
        'filter:filter1': {
            'filter-with': 'filter2',
            'use': 'egg:FakeApp#caps'
        },
        'filter:filter2': {
            'use': 'egg:FakeApp#caps'
        },
        'app:filtered-app': {
            'filter-with': 'filter',
            'use': 'package:FakeApp#basic_app'
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
