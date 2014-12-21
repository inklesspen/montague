import os
from montague.loadwsgi import Loader
from montague import load_app, load_server

here = os.path.dirname(__file__)


def test_read_config(fakeapp):
    ini_style_loader = Loader(os.path.join(here, 'config_files/simple_config.json_ini'))
    expected = {
        'application:main': {'use': 'package:FakeApp#basic_app'},
        'application:egg': {'use': 'egg:FakeApp#other'},
        'server:server_factory': {
            'port': 42,
            'use': 'egg:FakeApp#server_factory',
        },
        'server:server_runner': {
            'host': '127.0.0.1',
            'use': 'egg:FakeApp#server_runner'
        },
    }

    assert ini_style_loader.config == expected

    json_style_loader = Loader(os.path.join(here, 'config_files/simple_config.json'))
    expected = {
        'application': {
            'egg': {'use': 'egg:FakeApp#other'},
            'main': {'use': 'package:FakeApp#basic_app'}
        },
        'server': {
            'server_factory': {'port': 42,
                               'use': 'egg:FakeApp#server_factory'},
            'server_runner': {'host': '127.0.0.1',
                              'use': 'egg:FakeApp#server_runner'}
        }
    }

    assert json_style_loader.config == expected
    assert json_style_loader.config_loader.ini_config() == \
        ini_style_loader.config_loader.ini_config()


def test_load_app(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is fakeapp.apps.basic_app
    assert app2 is fakeapp.apps.basic_app2


def test_load_server(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    server = load_server(config_path, name='server_factory')
    actual = server(fakeapp.apps.basic_app)
    assert actual.montague_conf['local_conf']['port'] == 42
    resp = actual.get('/')
    assert b'This is basic app' == resp.body
    server = load_server(config_path, name='server_runner')
    actual = server(fakeapp.apps.basic_app2)
    assert actual.montague_conf['local_conf']['host'] == '127.0.0.1'
    resp = actual.get('/')
    assert b'This is basic app2' == resp.body
