CC=g++ $(COMPILER_OPTIONS)
COMPILER_OPTIONS=-std=c++11 -g

TOP = ..
INCLUDE = $(TOP)/include
BIN = bin
SRC = $(TOP)/src


all: 

	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/Reconstruction.o $(SRC)/Reconstruction.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/Parameters.o $(SRC)/Parameters.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/State.o $(SRC)/State.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/RecWrap.o $(SRC)/RecWrap.cpp

	$(CC) -shared -Wl,-soname,$(abspath ../lib/libcdi.so) -o $(abspath ../lib/libcdi.so) $(BIN)/Reconstruction.o $(BIN)/Parameters.o $(BIN)/State.o $(BIN)/RecWrap.o -lc

