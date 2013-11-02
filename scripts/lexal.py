# -*- mode: python, coding: utf-8 -*-
#
# pony-initialisation lexal functions
#


def sh_lex(sh_file):
    '''
    Restricted shell variable assignment parsing
    
    @param   sh_file  File format as POSIX shell only containing variable assignments with restricted syntax
    @return           Map from variable name to variable value (string or list of strings)
    '''
    lines = None
    with open(sh_file, "r") as file:
        lines = file.read()
    lines = lines.decode("utf-8", "replace")
    
    comment = False
    bracket = None
    escape = False
    quote = None
    name = ''
    value = None
    rc = {}
    
    for c in lines:
        if comment:
            if c == '\n':
                comment = False
        elif escape:
            if c not in '\n\r\f':
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
                name = ""
                if value is not None:
                    rc[name] = value
                value = ""
            else:
                bracket.append(value)
                value = None
        elif c == '#':
            comment = True
        elif c == '\\':
            escape = True
        elif c in "\"'":
            value += '\0'
            quote = c
        elif value is None:
            if c == '=':
                value = ''
            else:
                name += c
        else:
            if c == '(':
                bracket = []
            elif c == ')':
                if not value == "":
                    bracket.append(value)
                rc[name] = [v.replace('\0', '') for v in bracket]
                bracket = None
                value = ""
                name = None
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
                cols.append(b.replace("\0", ""))
                buf = ""
            if (c == '\n') and (len(cols) > 0):
                if len(cols) < 4:
                    rc.append((cols + [""] * columns)[:colums])
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

