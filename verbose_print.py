import enum
from functools import partial


class _PrintLevel(enum.Enum):
    DEFAULT = 0
    VERBOSE = 1
    VERY_VERBOSE = 2


class _VerbosePrinter(object):

    def __init__(self):
        self.print_level = _PrintLevel.DEFAULT.value

    def print(self, message_print_level, message):
        if self.print_level >= message_print_level:
            print(message)


_verbose_printer = _VerbosePrinter()


def set_print_level(print_level):
    if print_level == 1:
        _verbose_printer.print_level = _PrintLevel.VERBOSE.value
    elif print_level >= 2:
        _verbose_printer.print_level = _PrintLevel.VERY_VERBOSE.value
    else:
        _verbose_printer.print_level = _PrintLevel.DEFAULT.value


print_v = partial(_verbose_printer.print, _PrintLevel.VERBOSE.value)
print_vv = partial(_verbose_printer.print, _PrintLevel.VERY_VERBOSE.value)
