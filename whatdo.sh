#!/bin/bash


grep -E -rHn -B 2 -A 2 "^\W*\sTODO" * | sed 's/--/\n-------------\n/g'
