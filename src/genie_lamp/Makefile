EXE=genie_lamp
FILES=main.cpy

# Build using rmkit's build system
# This is a standalone Makefile for the genie_lamp fork

# Default target
all: info

info:
	@echo "Genie-Lamp: Gesture launcher without rm2fb requirement"
	@echo ""
	@echo "This fork removes rm2fb dependency by using fixed screen dimensions."
	@echo "It integrates with lamp for programmatic drawing via gestures."
	@echo ""
	@echo "To build and install:"
	@echo "  1. cd ../../resources/rmkit"
	@echo "  2. ln -sf ../../src/genie_lamp src/"
	@echo "  3. cd src/genie_lamp"
	@echo "  4. make -f ../../Makefile compile TARGET=rm"
	@echo "  5. scp ../../build/genie_lamp root@10.11.99.1:/opt/bin/"
	@echo ""
	@echo "To install config:"
	@echo "  scp lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf"
	@echo ""
	@echo "To run on device:"
	@echo "  ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_lamp.conf"

# Include rmkit build system if called from rmkit directory
-include ../../actions.make

install:
	make copy
	make install_config

install_config:
	scp ./lamp_test.conf root@${HOST}:/opt/etc/genie_lamp.conf

.PHONY: all info install install_config
