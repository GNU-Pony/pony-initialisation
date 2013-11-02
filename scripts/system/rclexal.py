# -*- mode: python, coding: utf-8 -*-
#
# pony-initialisation lexal functions
#


def kernel_opts(option, converter):
    '''
    Parse an option with an argument from the kernel command line arguments
    
    @param   option     The option
    @param   converter  Function to convert the argument to a usable type
    @return             The option's argument, None if it did not exist,
                        did not have a value, or if the value as not parseable
    '''
    rc = None
    try:
        option += "="
        cmdline = None
        with open("£{PROC}/cmdline", "rb") as file:
            cmdline = file.read().decode("utf-8", "replace").replace("\n", "").split(" ")
        for opt in cmdline:
            if opt.startswith(option) and (opt != option):
                rc = opt[len(option):]
                break
        rc = rc if rc is None else converter(rc)
    except:
        rc = None
    return rc


def sh_lex(sh_file):
    '''
    Restricted shell variable assignment parsing
    
    @param   sh_file  File format as POSIX shell only containing variable assignments with restricted syntax
    @return           Map from variable name to variable value (string or list of strings)
    '''
    lines = None
    with open(sh_file, "rb") as file:
        lines = file.read()
    lines = lines.decode("utf-8", "replace")
    
    comment, bracket, escape, quote, name, value = False, None, False, None, "", None
    rc = {}
    
    for c in lines:
        if comment:
            if c == '\n':
                comment, bracket, escape, quote, name, value = False, None, False, None, "", None
        elif escape:
            if c not in "\n\r\f":
                value += c
        elif (quote is not None) and (c == quote):
            quote = None
        elif quote == '"':
            if c == '\\':
                escape = True
            else:
                value += c
        elif quote == '\'':
            value += c
        elif c in " \t\n\r\f":
            if bracket is None:
                if value is not None:
                    rc[name] = value.replace("\0", "")
                name, value = "", None
            else:
                bracket.append(value)
                value = ""
        elif c == '#':
            comment = True
        elif c == '\\':
            escape = True
        elif c in "\"'":
            value += "\0"
            quote = c
        elif value is None:
            if c == '=':
                value = ""
            else:
                name += c
        else:
            if c == '(':
                bracket = []
            elif c == ')':
                if not value == "":
                    bracket.append(value)
                rc[name] = [v.replace("\0", "") for v in bracket]
                name, value, bracket = "", None, None
            else:
                value += c
    
    return rc


def sh_tab(table, columns):
    '''
    Parse a table file which uses restricted shell syntax
    
    @param   table    Raw table file content
    @param   columns  The number of columns in the table
    @return           The table parsed
    '''
    rc = []
    cols = []
    comment = False
    escape = False
    quote = '\0'
    buf = ""
    for c in table + "\n":
        if comment:
            if c == '\n':
                comment = False
        elif escape:
            if c != '\n':
                buf += c
            escape = False
        elif (c == '\\') and (quote != '\''):
            escape = True
        elif quote != '\0':
            if c == quote:
                quote = '\0'
            else:
                buf += c
        elif c in " \t\n":
            if len(buf) != 0:
                cols.append(buf.replace("\0", ""))
                buf = ""
            if (c == '\n') and (len(cols) > 0):
                if len(cols) < 4:
                    rc.append((cols + [""] * columns)[:columns])
                else:
                    rc.append(cols)
                cols = []
        elif c in "\"'":
            quote = c
            buf += '\0'
        elif c == '#':
            comment = True
        else:
            buf += c
    return rc

