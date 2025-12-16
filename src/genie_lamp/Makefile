# Standalone Makefile for genie_lamp
# No rmkit dependencies - pure C++ compilation

CXX = arm-linux-gnueabihf-g++
CXXFLAGS = -O2 -std=c++11 -Wall
TARGET = genie_lamp
SOURCE = main.cpp

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)
	@echo "Build complete: $(TARGET)"
	@ls -lh $(TARGET)

clean:
	rm -f $(TARGET)

install: $(TARGET)
	scp $(TARGET) root@10.11.99.1:/opt/bin/
	@echo "Installed to remarkable at /opt/bin/$(TARGET)"

.PHONY: all clean install
