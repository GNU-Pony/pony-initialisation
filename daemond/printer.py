# -*- python -*-


import sys


printer_pipe = sys.stdout
'''
:iofile  Output pipe that keeps track of the line count
'''


def print_blacklisted(message):
    '''
    Print a message that a daemon is blacklisted
    
    @param  message:str  The message to print
    '''
    printer_print("01;35", message, "BLCK")


def print_starting(message):
    '''
    Print a message that a daemon is starting
    
    @param   message:str  The message to print
    @return  :int         The line the message is printed on
    '''
    return printer_print("01;33", message, "WAIT")


def print_failed(message, index):
    '''
    Print a message that a daemon failed to start
    
    @param  message:str  The message to print
    @param  index:int    The line to rewrite
    '''
    printer_print("01;31", message, "FAIL", index)


def print_successful(message, index):
    '''
    Print a message that a daemon started
    
    @param  message:str  The message to print
    @param  index:int    The line to rewrite
    '''
    printer_print("01;32", message, "DONE", index)



def printer_print(message, colour, status, index = None):
    '''
    Print a message
    
    @param   message:str  The message to print
    @param   colour:str   The ANSI colour of the message
    @param   status:str   Status message (hidden with colours), should always be of same length
    @param   index:int?   The line to rewrite, or `None` for a new line
    @return  :int         The line to message is printed on
    '''
    if USECOLOUR:
        print("\033[00;%sm%s\033[00m \033[30m[%s]\033[00m" % (colour, message, status))
    else:
        print("%s [%s]" % (message, status))
    return 0

