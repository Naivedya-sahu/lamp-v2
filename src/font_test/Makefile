EXE=font_test
FILES=main.cpy
APP=$(EXE)

# Paths - use realpath to get absolute paths
RMKIT_ROOT=$(realpath ../../resources/rmkit)
BUILD_DIR=$(RMKIT_ROOT)/src/build
CPP_DIR=$(RMKIT_ROOT)/src/.$(APP)_cpp
STB_OBJ=$(BUILD_DIR)/stb.arm.o

# Compilation flags
HOST?=10.11.99.1
TARGET?=rm
CROSS_TC?=arm-linux-gnueabihf
CXX_BIN?=$(CROSS_TC)-g++
CPP_FLAGS=-ldl -pthread -lpthread -fdata-sections -ffunction-sections -Wl,--gc-sections
RMKIT_IMPL="RMKIT_IMPLEMENTATION"
OKP_FLAGS=-ig $(RMKIT_IMPL) -ns -ni -for -d $(CPP_DIR)/ -o $(BUILD_DIR)/$(EXE) $(FILES)

compile:
ifeq ($(TARGET),rm)
	make compile_remarkable
else ifeq ($(TARGET),x86)
	make compile_x86
else
	make compile_remarkable
endif

compile_remarkable:
	CXX=$(CXX_BIN) okp $(OKP_FLAGS) $(STB_OBJ) -- -D"REMARKABLE=1" -D$(RMKIT_IMPL) $(CPP_FLAGS) -O2

compile_x86:
	CXX=g++ okp $(OKP_FLAGS) $(BUILD_DIR)/stb.x86.o -- -D$(RMKIT_IMPL) $(CPP_FLAGS)

default: compile

clean:
	rm -rf $(CPP_DIR)
	rm -f $(BUILD_DIR)/$(EXE)

.PHONY: compile compile_remarkable compile_x86 default clean
