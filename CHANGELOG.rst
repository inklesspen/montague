
Changelog
=========

0.2.0 (2015-06-14)
-----------------------------------------

* Remove the PasteDeploy FakeApp package in favor of ``montague_testapps``.
* Enable a ``looponfail`` tox environment.
* Add logging ini conversion
* Reincorporate the test JSON config loader, active only during tests.
* Remove the ``DEFAULT`` sentinal value; we'll use 'main' as the default loadable name, just like grandpa used to do. This is a breaking change.
* Add logging config to the Montague Standard Format.
* Allow config loaders to skip implementing ``app_config()`` and the like, instead of raising ``NotImplementedError``
* Add validation functions to let config loaders test their compliance. These functions use assert statements, making them ideal for py.test, but they should work under unittest as well.

0.1.5 (2015-05-12)
-----------------------------------------

* The legacy PasteDeploy support was spun off into a separate package (``montague_pastedeploy``), enabling simplicity.

0.1.0 (2014-11-12)
-----------------------------------------

* First release on PyPI, corresponding to PasteDeploy 1.5.2.
* Backwards incompatibility: ConfigMiddleware stores the config under ``montague.config`` in the environment instead of ``paste.config`` and no longer offers a threadlocal ``CONFIG`` importable. (This removes the dependency on Paste.)
