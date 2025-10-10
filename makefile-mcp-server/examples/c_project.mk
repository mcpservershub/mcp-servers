# C Project Makefile Example
# Demonstrates a typical C project build system

# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
LDFLAGS = -lm
AR = ar
ARFLAGS = rcs

# Directories
SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin
LIB_DIR = lib
TEST_DIR = tests
INCLUDE_DIR = include

# Target executable
TARGET = $(BIN_DIR)/myapp
LIBRARY = $(LIB_DIR)/libmyapp.a

# Source files
SOURCES = $(wildcard $(SRC_DIR)/*.c)
OBJECTS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SOURCES))
TEST_SOURCES = $(wildcard $(TEST_DIR)/*.c)
TEST_BINS = $(patsubst $(TEST_DIR)/%.c,$(BIN_DIR)/test_%,$(TEST_SOURCES))

# Include paths
INCLUDES = -I$(INCLUDE_DIR)

# Default target
.DEFAULT_GOAL := all

# Phony targets
.PHONY: all clean test install uninstall lib debug release help dirs check format

# Main targets
all: dirs $(TARGET)

lib: dirs $(LIBRARY)

debug: CFLAGS += -DDEBUG -O0
debug: all

release: CFLAGS += -DNDEBUG -O3
release: all

# Create necessary directories
dirs:
	@mkdir -p $(OBJ_DIR) $(BIN_DIR) $(LIB_DIR)

# Build executable
$(TARGET): $(OBJECTS)
	@echo "Linking $@..."
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)
	@echo "Build complete: $@"

# Build static library
$(LIBRARY): $(OBJECTS)
	@echo "Creating static library $@..."
	$(AR) $(ARFLAGS) $@ $^
	@echo "Library created: $@"

# Compile source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Build and run tests
test: $(TEST_BINS)
	@echo "Running tests..."
	@for test in $(TEST_BINS); do \
		echo "Running $$test..."; \
		$$test || exit 1; \
	done
	@echo "All tests passed!"

$(BIN_DIR)/test_%: $(TEST_DIR)/%.c $(LIBRARY)
	@echo "Building test $@..."
	$(CC) $(CFLAGS) $(INCLUDES) $< -L$(LIB_DIR) -lmyapp -o $@ $(LDFLAGS)

# Code quality checks
check:
	@echo "Running static analysis..."
	@which cppcheck > /dev/null && cppcheck --enable=all --suppress=missingIncludeSystem $(SRC_DIR) || echo "cppcheck not installed"
	@which clang-tidy > /dev/null && clang-tidy $(SOURCES) -- $(CFLAGS) $(INCLUDES) || echo "clang-tidy not installed"

# Format code
format:
	@echo "Formatting code..."
	@which clang-format > /dev/null && clang-format -i $(SOURCES) $(wildcard $(INCLUDE_DIR)/*.h) || echo "clang-format not installed"

# Installation
PREFIX ?= /usr/local
install: $(TARGET)
	@echo "Installing to $(PREFIX)..."
	install -d $(PREFIX)/bin
	install -m 755 $(TARGET) $(PREFIX)/bin
	@echo "Installation complete"

uninstall:
	@echo "Removing from $(PREFIX)..."
	rm -f $(PREFIX)/bin/$(notdir $(TARGET))
	@echo "Uninstallation complete"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(OBJ_DIR) $(BIN_DIR) $(LIB_DIR)
	@echo "Clean complete"

# Generate documentation
docs:
	@echo "Generating documentation..."
	@which doxygen > /dev/null && doxygen Doxyfile || echo "doxygen not installed"

# Dependency generation
-include $(OBJECTS:.o=.d)

$(OBJ_DIR)/%.d: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) $(INCLUDES) -MM -MT '$(OBJ_DIR)/$*.o' $< > $@

# Help target
help:
	@echo "Available targets:"
	@echo "  all      - Build the main executable (default)"
	@echo "  lib      - Build static library"
	@echo "  debug    - Build with debug symbols and assertions"
	@echo "  release  - Build with optimizations"
	@echo "  test     - Build and run tests"
	@echo "  check    - Run static analysis tools"
	@echo "  format   - Format source code"
	@echo "  docs     - Generate documentation"
	@echo "  install  - Install the executable (PREFIX=$(PREFIX))"
	@echo "  uninstall- Remove installed executable"
	@echo "  clean    - Remove all build artifacts"
	@echo "  help     - Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  CC=$(CC)"
	@echo "  CFLAGS=$(CFLAGS)"
	@echo "  PREFIX=$(PREFIX)"

# Print variables for debugging
print-%:
	@echo "$* = $($*)"