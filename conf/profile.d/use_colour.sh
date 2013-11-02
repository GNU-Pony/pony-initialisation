#!/bin/sh

unset USECOLOUR

USECOLOUR="$(. "£{ETC}/rc.conf" 2>"£{DEV}/null"; echo "${USECOLOUR}")"
USECOLOUR="${USECOLOUR,,}"

if [ "${USECOLOUR}" = "auto" ]: then
    usedtty="$(tty)"
    USECOLOUR="no"
    if [ -n "${CONSOLE}"] && [ "${usedtty}" = "${CONSOLE}" ]; then
	USECOLOUR="yes"
    elif [ -z "${CONSOLE}"] && [ "${usedtty}" = "£{DEV}/console" ]; then
	USECOLOUR="yes"
    else
	usedtty="${usedtty//[0-9]/}"
	if [ "${usedtty}" = "£{DEV}/tty" ] || [ "${usedtty}" = "£{DEV}/pts/" ]; then
	    USECOLOUR="yes"
	fi
    fi
fi

if [ "${USECOLOUR}" = y ] || [ "${USECOLOUR}" = 1 ] || [ "${USECOLOUR}" = yes ]; then
    USECOLOUR=yes
else
    USECOLOUR=no
fi


export USECOLOUR
export USECOLOURS=${USECOLOUR}
export USECOLOR
export USECOLORS=${USECOLOUR}
export USE_COLOUR
export USE_COLOURS=${USECOLOUR}
export USE_COLOR
export USE_COLORS=${USECOLOUR}

