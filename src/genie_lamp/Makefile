EXE=genie_lamp
FILES=main.cpy

# This Makefile requires LAMP_V2_ROOT to be set due to spaces in the path
# Use: LAMP_V2_ROOT="$(cd ../.. && pwd)" make
# Or use the build_and_deploy.sh script

ifndef LAMP_V2_ROOT
    $(error LAMP_V2_ROOT is not set. Run: LAMP_V2_ROOT=$$(cd ../.. && pwd) make)
endif

RMKIT_SRC := $(LAMP_V2_ROOT)/resources/rmkit/src
BUILD_DIR := $(RMKIT_SRC)/build

# Build settings
HOST?=10.11.99.1
CROSS_TC?=arm-linux-gnueabihf
CXX_BIN?=$(CROSS_TC)-g++
APP=$(EXE)

# Compiler flags
CPP_FLAGS=-ldl -pthread -lpthread -fdata-sections -ffunction-sections -Wl,--gc-sections -O2

# Default target
all: compile_remarkable

stb_obj:
	mkdir -p "$(BUILD_DIR)"
	"$(CXX_BIN)" -c "$(RMKIT_SRC)/vendor/stb/stb.cpp" -o "$(BUILD_DIR)/stb.arm.o" -fPIC -Os

compile_remarkable: stb_obj
	CXX="$(CXX_BIN)" okp -ig "RMKIT_IMPLEMENTATION" -ns -ni -for -d "$(RMKIT_SRC)/.$(APP)_cpp/" -o "$(BUILD_DIR)/$(EXE)" $(FILES) "$(BUILD_DIR)/stb.arm.o" -- -D"REMARKABLE=1" -D"RMKIT_IMPLEMENTATION" $(CPP_FLAGS)

install:
	make copy
	make install_config

install_config:
	scp ./genie_lamp.conf root@${HOST}:/opt/etc/genie_lamp.conf
