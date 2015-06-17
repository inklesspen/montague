import os
from montague.loadwsgi import Loader
from montague.testjson import JSONConfigLoader

here = os.path.dirname(__file__)


def test_file_extensions(working_set):
    loader = Loader(os.path.join(here, 'config_files/simple_config.json'))
    assert isinstance(loader.config_loader, JSONConfigLoader)
    loader = Loader(os.path.join(here, 'config_files/multiple_extensions.test.sample.json'))
    assert isinstance(loader.config_loader, JSONConfigLoader)
