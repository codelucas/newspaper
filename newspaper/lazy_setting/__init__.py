
__author__ = "wcsjtu"

__version__ = "0.0.1"
from importlib import import_module
from . import conf, global_settings, module_loading

def dymatic_import(path):
    cf = path.split(".")
    cf_l = ".".join(cf[:-1])
    cookie_fac = import_module(cf_l)
    cls_or_func = getattr(cookie_fac, cf[-1])
    return cls_or_func


__all__ = ["conf","__version__","dymatic_import"]