# Simple font test - no rmkit/rm2fb dependencies
# Just validates font loading with stb_truetype

CXX = g++
CXXFLAGS = -std=c++17 -Wall -O2
STB_DIR = ../../resources/rmkit/src/vendor/stb

# For cross-compilation to RM2 ARM
ARM_CXX = arm-linux-gnueabihf-g++
ARM_FLAGS = -std=c++17 -static -O2

font_test: main.cpy
	$(CXX) $(CXXFLAGS) -I$(STB_DIR) main.cpy \
		$(STB_DIR)/stb.cpp \
		-o font_test

arm: main.cpy
	$(ARM_CXX) $(ARM_FLAGS) -I$(STB_DIR) main.cpy \
		$(STB_DIR)/stb.cpp \
		-o font_test.arm

clean:
	rm -f font_test font_test.arm

test: font_test
	./font_test

.PHONY: arm clean test
