import os
import sys
import shutil

from pkg_resources import working_set, require
import pytest


@pytest.fixture(scope='session')
def fakeapp():
    test_dir = os.path.dirname(__file__)
    egg_info_dir = os.path.join(
        test_dir, 'fake_packages', 'FakeApp.egg', 'EGG-INFO')
    info_dir = os.path.join(
        test_dir, 'fake_packages', 'FakeApp.egg', 'FakeApp.egg-info-dir')
    if not os.path.exists(egg_info_dir):
        try:
            os.symlink(info_dir, egg_info_dir)
        except:
            shutil.copytree(info_dir, egg_info_dir)

    sys.path.append(os.path.dirname(egg_info_dir))

    working_set.add_entry(os.path.dirname(egg_info_dir))
    require('FakeApp')
    import fakeapp as fa
    return fa
