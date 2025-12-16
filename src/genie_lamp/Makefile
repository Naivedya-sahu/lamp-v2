# Standalone Makefile for genie_lamp
# No rmkit dependencies - pure C++ compilation

CXX = arm-linux-gnueabihf-g++
CXXFLAGS = -O2 -std=c++11 -Wall
TARGET = genie_lamp
SOURCE = main.cpp
HOST ?= 10.11.99.1

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)
	@echo "Build complete: $(TARGET)"
	@ls -lh $(TARGET)

clean:
	rm -f $(TARGET)

install: $(TARGET)
	scp $(TARGET) root@$(HOST):/opt/bin/
	scp genie_lamp.conf root@$(HOST):/opt/etc/
	scp genie_lamp.service root@$(HOST):/etc/systemd/system/
	@echo "Installed to remarkable at /opt/bin/$(TARGET)"

enable:
	ssh root@$(HOST) systemctl daemon-reload
	ssh root@$(HOST) systemctl enable genie_lamp.service
	@echo "Service enabled - will start on boot"

start:
	ssh root@$(HOST) systemctl start genie_lamp.service
	@echo "Service started"

stop:
	ssh root@$(HOST) systemctl stop genie_lamp.service
	@echo "Service stopped"

status:
	ssh root@$(HOST) systemctl status genie_lamp.service

logs:
	ssh root@$(HOST) journalctl -u genie_lamp.service -f

.PHONY: all clean install enable start stop status logs
