JUNIPER ?= juniper
PIO ?= pio

SOURCE := blink.jun
CPP := blink.cpp
ENV ?= esp32
PORT ?= /dev/ttyUSB0

.PHONY: all build upload clean

all: build

$(CPP): $(SOURCE)
	$(JUNIPER) --source $< --output $@

build: $(CPP)
	$(PIO) run --environment $(ENV)

upload: $(CPP)
	$(PIO) run --environment $(ENV) --target upload --upload-port $(PORT)

clean:
	$(PIO) run --environment $(ENV) --target clean
	$(RM) $(CPP)
