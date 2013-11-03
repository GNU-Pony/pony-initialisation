# -*- python -*-


import os
import grp
import time
import fcntl
import socket

from printer import *


server = None


start_printer()


def already_running():
    '''
    Finds out whether daemond is already running
    
    @return  Whether daemond is already running
    '''
    if os.path.exists("£{RUN}/daemond/daemond.pid"):
        with open("£{RUN}/daemond/daemond.pid", "r") as file:
            try:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    fcntl.flock(file.fileno(), fcntl.LOCK_UN)
                except:
                    pass
            except:
                return True
    return False


def create_pidfile():
    '''
    Create and lock PID file
    '''
    if not os.path.exists("£{RUN}/daemond"):
        os.mkdir("£{RUN}/daemond")
    pidfile = open("£{RUN}/daemond/daemond.pid", "wb") ## Must not be closed
    pidfile.write(("%i\n" % os.getpid()).encode("utf-8"))
    pidfile.flush()
    fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX)


def create_socket():
    '''
    Create daemond interprocess domain socket
    '''
    global server, server_unpriv
    if not os.path.exists("£{RUN}/daemond"):
        os.mkdir("£{RUN}/daemond")
    def create_(sockname, mode):
        if os.path.exists(sockname):
            os.unlink(sockname)
        server_ = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_.bind(sockname)
        os.chmod(sockname, mode)
        server_.listen(int(os.getenv("DAEMOND_BACKLOG", "4")))
        return server_
    server = create_("£{RUN}/daemond/server", 0o750)
    try:
        server.chown("£{RUN}/daemond/server", 0, grp.getgrnam('daemons').gr_gid);
    except:
        pass # Probably got KeyError because the group did not exist


def accept_connection():
    '''
    Waits for a new client and returns a socket connect to it
    
    @return  :socket  The next client in the queue
    '''
    return server.accept()[0]


def signal_daemond(verb, started, auto, start_daemons, use_colour):
    '''
    Send a signal to daemond
    
    @param   verb:str                The verb to send
    @param   started:boolean?        Started daemon filter value to send
    @param   auto:boolean?           Autostarted daemon filter value to send
    @param   start_daemons:itr<str>  Daemons to send
    @param   use_colour:boolean      Whether to use colours
    @return  :int                    Number of failures
    '''
    fails, done = 0, 0
    message = "%s\0%s%s%s%s\0\0"
    def _b(boolean):
        if boolean is None:
            return "B"
        return "T" if boolean else "F"
    message %= (verb, _b(started), _b(auto), _b(use_colour), "\0".join(start_daemons))
    message = message.encode("utf-8")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("£{RUN}/daemond/server")
    client.sendall(message)
    linemap = {}
    pipe = None
    def pipe_thread():
        global pipe
        pipe_flags = fcntl.fcntl(pipe, fcntl.F_GETFL)
        fcntl.fcntl(pipe, fcntl.F_SETFL, pipe_flags | os.O_NONBLOCK)
        while True:
            data = pipe.read()
            if len(data) == 0:
                time.sleep(1)
            printer_pipe.write(data)
            printer_pipe.flush()
    buf = ""
    while True:
        data = client.recv(32)
        if len(data) == 0:
            time.sleep(0.5) # Should not happen
            continue
        for c in data:
            if c == '\0':
                signal_type = buf[0]
                signal_value = buf[1:]
                buf = ""
                if signal_type == 'P':
                    pipe = open(signal_value, "rb")
                    t = Thread(target = pipe_thread)
                    t.daemon = True
                    t.start()
                elif signal_type == 'B':
                    print_blacklisted("%s is blacklisted" % daemon.name)
                    fails += 1
                    done += 1
                elif signal_type == 'S':
                    message = "Sending %s signal to %s" % (verb[0].upper() + verb[1:], signal_value)
                    linemap[signal_value] = print_starting(message)
                    done += 1
                elif signal_type == 'F':
                    fails += 1
                    done += 1
                    message = "Sending %s signal to %s" % (verb[0].upper() + verb[1:], signal_value)
                    print_failed(message, linemap[signal_value])
                elif signal_type == 'D':
                    done += 1
                    message = "Sending %s signal to %s" % (verb[0].upper() + verb[1:], signal_value)
                    print_successful(message, linemap[signal_value])
                elif signal_type == 'X':
                    if pipe is not None:
                        pipe.close()
                    client.close()
                    return 0
                if done == len(start_daemons):
                    if pipe is not None:
                        pipe.close()
                    client.sendall(b'\0')
                    client.close()
                    return fails
            else:
                buf += c

