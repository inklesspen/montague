from pprint import pprint
import sys

import pkg_resources

from six import print_


def test_load_package():
    print_('Path:')
    pprint(sys.path)
    print_(pkg_resources.require('FakeApp'))
