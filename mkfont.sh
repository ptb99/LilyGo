#! /bin/sh

###
### Make a bitmap font from a TT/etc scalable font (for use w/ CircuitPython)
###

Usage() {
    echo "usage: mkfont.sh FONTFILE SIZE"
    echo "    ex: /usr/share/fonts/gnu-free/FreeSans.ttf 24"
    exit 2
}


SRC=$1
SIZE=$2
ext=${SRC##*.}
OUT=$(basename ${SRC} .${ext})-${SIZE}.pcf

[ -f ${SRC} ] || Usage
[ ${SIZE} -gt 0 ] || Usage

echo "otf2bdf -p ${SIZE} ${SRC} | bdftopcf > ${OUT}"
otf2bdf -p ${SIZE} ${SRC} | bdftopcf > ${OUT}


# Good fonts (use ftstring):
#/usr/share/fonts/urw-base35/NimbusSansNarrow-Regular.otf
#/usr/share/fonts/google-noto/NotoSans-CondensedMedium.ttf
#/usr/share/fonts/gnu-free/FreeSans.ttf
