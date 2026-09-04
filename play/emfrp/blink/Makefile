EMFRP ?= emfrp

SOURCE := blink.mfrp
PORT ?= /dev/ttyUSB0

.PHONY: all build upload clean

all: build

gen: $(SOURCE)
	$(EMFRP) --cpp --nomain $<

build:
	arduino-cli compile --fqbn esp32:esp32:esp32 .

upload: build
	arduino-cli upload --fqbn esp32:esp32:esp32 --port $(PORT) .
