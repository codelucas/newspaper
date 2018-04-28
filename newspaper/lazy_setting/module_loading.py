import sys
from importlib import import_module


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    eles = dotted_path.rsplit('.', 1)
    l = len(eles)
    if l == 2:
        module_path, class_name = eles
        module = import_module(module_path)
        try:
            return getattr(module, class_name)
        except AttributeError:
            msg = 'Module "%s" does not define a "%s" attribute/class' % (
                module_path, class_name)
        raise ImportError(msg, None, sys.exc_info()[2])
    elif l == 1:
        module = import_module(dotted_path)
        return module

__all__ = ["import_string", "import_module"]