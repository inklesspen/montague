import os
from montague.ini import IniConfigLoader
from montague import load_app, load_server

here = os.path.dirname(__file__)


def test_read_config():
    config = IniConfigLoader(os.path.join(here, 'ini_files/simple_config.ini'))
    assert config.config() == {
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
    }


def test_load_app(fakeapp):
    config_path = os.path.join(here, 'ini_files/simple_config.ini')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is fakeapp.apps.basic_app
    assert app2 is fakeapp.apps.basic_app2


def test_load_server(fakeapp):
    config_path = os.path.join(here, 'ini_files/simple_config.ini')
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