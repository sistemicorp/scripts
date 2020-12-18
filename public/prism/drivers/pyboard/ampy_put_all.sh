#!/usr/bin/env bash

usage () {
  echo "Usage: ampy_put_all.sh <port> <slot>"
  echo ""
  echo "Copy all iba01 files to PyBoard on port <port>"
  echo "The PyBoard filesystem should be reset before doing this."
  echo ""
  echo "Where: port = 0,1,2,3, ... (the # in /drv/ttyACM#)"
  echo "Where: slot = 0,1,2,3"
}

if [[ $1 == "--help" ]] || [[ $1 == "" ]] ; then
  usage
  exit 0
fi

rm -rf ./sd_image/__pycache__ 2> /dev/null

if [[ $# -ne 2 ]]; then
    echo "Illegal number of parameters, use --help"
    exit 2
fi

for f in ./sd_image/*
do
	echo "Copying file - $f"
	ampy --port /dev/ttyACM$1 put $f
done

rm ./sd_image/SLOT* 2> /dev/null
touch ./sd_image/SLOT$2
echo "Copying file - SLOT$2"
ampy --port /dev/ttyACM$1 put ./sd_image/SLOT$2
rm ./sd_image/SLOT* 2> /dev/null
