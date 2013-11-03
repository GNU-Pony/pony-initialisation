# -*- python -*-


import os
import sys
import time
import fcntl
from threading import Thread, Lock



printer_lock = None
printer_line = 0
printer_rows = None
printer_thread = None
printer_interal_pipe = None

printer_pipe = None
'''
:ofile  Output pipe that keeps track of the line count
'''


def print_thread():
    '''
    Printer thread function
    '''
    global printer_line, printer_lock, printer_interal_pipe
    while True:
        data = printer_interal_pipe.read()
        if len(data) == 0:
            time.sleep(1) # Should not happen, it should block iff it is empty
        n = 0
        for i in range(len(data)):
            if data[i] == '\n':
                n += 1
        printer_lock.acquire()
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        printer_line += n
        printer_lock.release()
    


def start_printer():
    '''
    Start printer thread, do this in the child process at the fork
    '''
    global printer_lock, printer_line, printer_rows, printer_thread, printer_interal_pipe, printer_pipe
    
    (printer_interal_pipe, printer_pipe) = os.pipe()
    printer_interal_pipe = fdopen(printer_interal_pipe, "rb")
    printer_pipe         = fdopen(printer_pipe,         "wb")
    pipe_flags           = fcntl.fcntl(printer_interal_pipe, fcntl.F_GETFL)
    fcntl.fcntl(printer_interal_pipe, fcntl.F_SETFL, pipe_flags | os.O_NONBLOCK)
    
    printer_rows = int(os.popen("stty size", "r").read().split(" ")[0])
    
    printer_lock = Lock()
    printer_thread = Thread(target = print_thread)
    printer_thread.start()




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
    global printer_line, printer_lock, printer_rows
    if FORKED_OF:
        index = None
    if USECOLOUR:
        msglen = len(message) + len(status) + 3
        message = "\033[00;%sm%s\033[00m \033[30m[%s]\033[00m" % (colour, message, status)
        printer_lock.acquire()
        if index is not None:
            diff = printer_line - index
            if diff >= printer_rows:
                printer_line += 1
                message += "\nn"
            else:
                message = "\033[%iA%s\033[%iD\033[%iB" % (diff, message, msglen, diff)
        else:
            index = printer_line
            printer_line += 1
            message += "\n"
        sys.stdout.buffer.write(message.encode("utf-8"))
        sys.stdout.buffer.flush()
        printer_lock.release()
    else:
        print("%s [%s]" % (message, status))
    return index

