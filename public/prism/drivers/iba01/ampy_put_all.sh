#!/usr/bin/env bash

usage () {
  echo "Usage: ampy_put_all.sh <port>"
  echo ""
  echo "Copy all iba01 files to PyBoard on port <port>"
  echo ""
  echo "Where: port = 0,1,2,3, ... (the # in /drv/ttyACM#)"
}

if [[ $1 == "--help" ]] || [[ $1 == "" ]] ; then
  usage
  exit 0
fi

for f in iba01_*.py
do
	echo "Copying file - $f"
	ampy --port /dev/ttyACM$1 put $f
done
