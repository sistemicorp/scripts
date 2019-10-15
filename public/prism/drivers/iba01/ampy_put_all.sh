#!/usr/bin/env bash

for f in iba01_*.py
do
	echo "Copying file - $f"
	ampy --port /dev/ttyACM0 put $f
done
