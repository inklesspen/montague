import os
from montague.ini import IniConfigLoader
from montague import load_app

here = os.path.dirname(__file__)


def test_read_config():
    config = IniConfigLoader(os.path.join(here, 'ini_files/simple_config.ini'))
    assert config.config() == {
        'application:main': {'use': 'package:FakeApp#basic_app'},
        'application:egg': {'use': 'egg:FakeApp#other'}
    }


def test_load_app(fakeapp):
    config_path = os.path.join(here, 'ini_files/simple_config.ini')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is fakeapp.apps.basic_app
    assert app2 is fakeapp.apps.basic_app2
