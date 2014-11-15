
Changelog
=========

0.1.0 (2014-11-12)
-----------------------------------------

* First release on PyPI, corresponding to PasteDeploy 1.5.2.
* Backwards incompatibility: ConfigMiddleware stores the config under ``montague.config`` in the environment instead of ``paste.config`` and no longer offers a threadlocal ``CONFIG`` importable. (This removes the dependency on Paste.)
