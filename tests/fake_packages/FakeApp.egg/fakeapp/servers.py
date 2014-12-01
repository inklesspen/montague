# Servers
import webtest


class TestServer(object):
    def __init__(self, global_conf, local_conf):
        self.global_conf = global_conf
        self.local_conf = local_conf

    def __call__(self, wsgi_app):
        test_app = webtest.TestApp(wsgi_app)
        test_app.montague_conf = dict(global_conf=self.global_conf,
                                      local_conf=self.local_conf)
        return test_app


def make_server_factory(global_conf, **local_conf):
    return TestServer(global_conf, local_conf)


def make_server_runner(wsgi_app, global_conf, **local_conf):
    return make_server_factory(global_conf, **local_conf)(wsgi_app)
