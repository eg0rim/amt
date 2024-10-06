# resource and ui compilers
UIC = pyside6-uic
RCC = pyside6-rcc
# python
PYTHON = python3

# dirs
UI_DIR = amt/views/ui
RCC_DIR = amt/views/resources
BUILD_DIR = amt/views/build

# file
UI_FILES = $(wildcard $(UI_DIR)/*.ui)
RCC_FILES = $(wildcard $(RCC_DIR)/*.qrc)

# output
UI_PY_FILES = $(patsubst $(UI_DIR)/%.ui, $(BUILD_DIR)/%_ui.py, $(UI_FILES))
RCC_PY_FILES = $(patsubst $(RCC_DIR)/%.qrc, $(BUILD_DIR)/%_qrc.py, $(RCC_FILES))

# all target
all: $(UI_PY_FILES) $(RCC_PY_FILES)

# ui files compile
$(BUILD_DIR)/%_ui.py: $(UI_DIR)/%.ui
	@mkdir -p $(BUILD_DIR)
	$(UIC) $< -o $@
	@echo "Compiled $< to $@"

# qrc files compile
$(BUILD_DIR)/%_qrc.py: $(RCC_DIR)/%.qrc
	@mkdir -p $(BUILD_DIR)
	$(RCC) $< -o $@
	@echo "Compiled $< to $@"

clean:
	rm -rf $(BUILD_DIR)
	@echo "Cleaned build directory"

.PHONY: all clean