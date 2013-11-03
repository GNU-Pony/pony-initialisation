# -*- python -*-


printer_pipe = sys.stdout


def print_blacklisted(message):
    printer_print("01;35", message, "BLCK")


def print_starting(message):
    return printer_print("01;33", message, "WAIT")


def print_failed(message, index):
    printer_print("01;31", message, "FAIL", index)


def print_successful(message, index):
    printer_print("01;32", message, "DONE", index)


def printer_print(message, colour, status, index = None):
    if USECOLOUR:
        print("\033[00;%sm%s\033[00m \033[30m[%s]\033[00m" % (colour, message, status))
    else:
        print("%s [%s]" % (message, status))
    return 0

