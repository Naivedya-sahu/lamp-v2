EXE=genie_lamp
FILES=main.cpy

# When run from src/genie_lamp, redirect to rmkit build system
.DEFAULT_GOAL := build

build:
	@echo "Building from rmkit directory..."
	@cd ../../resources/rmkit && make genie_lamp TARGET=rm

clean:
	@cd ../../resources/rmkit && rm -f src/build/genie_lamp

# Only include actions.make if we're in the rmkit directory structure
ifneq (,$(wildcard ../actions.make))
include ../actions.make

install:
	make copy
	make install_config

install_config:
	scp ./lamp_test.conf root@${HOST}:/opt/etc/genie_lamp.conf
endif
