EXE=genie_lamp
FILES=main.cpy gesture_parser.cpy

include ../actions.make

install:
	make copy
	make install_config

install_config:
	scp ./genie_lamp.conf root@${HOST}:/opt/etc/genie_lamp.conf
