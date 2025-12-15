EXE=genie_lamp
FILES=main.cpy
#ASSET_DIR=assets/

include ../actions.make

install:
	make copy
	make install_config

install_config:
	scp ./lamp_test.conf root@${HOST}:/opt/etc/genie_lamp.conf
