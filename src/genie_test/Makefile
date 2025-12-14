RMKIT_DIR = ../../resources/rmkit

genie_test:
	cd $(RMKIT_DIR) && make genie_test
	cp $(RMKIT_DIR)/src/build/genie_test .

clean:
	rm -f genie_test
	cd $(RMKIT_DIR) && make clean

.PHONY: genie_test clean
