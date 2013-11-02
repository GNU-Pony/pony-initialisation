#!/bin/sh

unset LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES \
      LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT LC_IDENTIFICATION

LOCALE="$(. "£{ETC}/rc.conf" 2>"£{DEV}/null"; echo "$LOCALE")"

if [ -n "${LOCALE}" ]; then
  LANG="${LOCALE}"
elif [ -n "${XDG_CONFIG_HOME}" ] && [ -r "${XDG_CONFIG_HOME}/locale.conf" ]; then
  . "${XDG_CONFIG_HOME}/locale.conf"
elif [ -n "$HOME" ] && [ -r "${HOME}/.config/locale.conf" ]; then
  . "${HOME}/.config/locale.conf"
elif [ -r "£{ETC}/locale.conf" ]; then
  . "£{ETC}/locale.conf"
fi

export LANG="${LANG:-C}"
[ -n "${LC_CTYPE}" ]          && export LC_CTYPE
[ -n "${LC_NUMERIC}" ]        && export LC_NUMERIC
[ -n "${LC_TIME}" ]           && export LC_TIME
[ -n "${LC_COLLATE}" ]        && export LC_COLLATE
[ -n "${LC_MONETARY}" ]       && export LC_MONETARY
[ -n "${LC_MESSAGES}" ]       && export LC_MESSAGES
[ -n "${LC_PAPER}" ]          && export LC_PAPER
[ -n "${LC_NAME}" ]           && export LC_NAME
[ -n "${LC_ADDRESS}" ]        && export LC_ADDRESS
[ -n "${LC_TELEPHONE}" ]      && export LC_TELEPHONE
[ -n "${LC_MEASUREMENT}" ]    && export LC_MEASUREMENT
[ -n "${LC_IDENTIFICATION}" ] && export LC_IDENTIFICATION
