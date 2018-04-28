# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os, sys
import importlib
from . import global_settings

ENVIRONMENT_VARIABLE = "NEWSPAPER_SETTING_MODULE"

SETTINGS_MODULE = os.environ.get(ENVIRONMENT_VARIABLE,"settings")

empty = object()

class ImproperlyConfigured(Exception):pass


def inner_method(method):
    def _inner(self, *args):
        self._setup_ifnot_exist()
        return method(self._wrapped, *args)


class LazySettings(object):
    """docstring for LazyObject"""

    _wrapped = None


    def __init__(self):
        self._wrapped = empty

    def __setattr__(self, name, value):
        if name == "_wrapped":
            self.__dict__[name] = value
        else:
            self._setup_ifnot_exist()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        self._setup_ifnot_exist()
        delattr(self._wrapped, name)

    def __getattr__(self, name):
        self._setup_ifnot_exist()
        return getattr(self._wrapped, name)

    @property
    def _empty(self):
        return True if self._wrapped is empty else False

    def _setup_ifnot_exist(self):
        if self._empty:
            self._setup()

    def _setup(self):
        
        if not SETTINGS_MODULE:
            raise ImproperlyConfigured(
                "Requested settings, but settings are not configured. "
                "You must either define the environment variable %s. "
                %  ENVIRONMENT_VARIABLE)

        self._wrapped = Settings(SETTINGS_MODULE)

    def configure(self, default_settings=global_settings, **options):
        """manually config"""
        raise NotImplementedError("unlike django setting, this setting module doesn't support manually config. \
        The unique way to config attr is in setting_module file")


class Settings(object):

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        try:
            object.__getattr__(self, name)
        except AttributeError:
            msg = "module `%s` object has no attribute `%s`." % (SETTINGS_MODULE, name)
            raise AttributeError( msg, sys.exc_info()[2])




    def __init__(self, settings_module):

        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        # customed settings
        self.SETTINGS_MODULE = settings_module
        mod = importlib.import_module(settings_module)

        self._explicit_settings = set()

        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)


    def is_overridden(self, setting):
        return setting in self._explicit_settings


    def __repr__(self):
        return '<%(cls)s "%(settings_module)s">' % {
            'cls': self.__class__.__name__,
            'settings_module': self.SETTINGS_MODULE,
        }


settings = LazySettings()

__all__ = ["settings"]