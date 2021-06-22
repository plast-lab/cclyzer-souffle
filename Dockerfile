FROM ubuntu:latest

WORKDIR /workdir
RUN apt-get -y update

# Build and install souffle
RUN apt-get -y install autoconf automake bison build-essential clang doxygen flex g++ git libffi-dev libncurses5-dev libtool libsqlite3-dev make mcpp python sqlite zlib1g-dev
RUN git clone https://github.com/souffle-lang/souffle.git
RUN cd souffle && \
    ./bootstrap && \
    ./configure && \
    make -j && \
    make install

# Build and install cclyzer
RUN apt-get -y install llvm
RUN apt-get -y install libclang-dev python-dev build-essential libboost-dev libboost-filesystem-dev libboost-program-options-dev libboost-python-dev
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python38.so /usr/lib/x86_64-linux-gnu/libboost_python.so

ADD . cclyzer-souffle
RUN cd cclyzer-souffle && \
    make clean && \
    make -j

ENTRYPOINT [ "/workdir/cclyzer-souffle/cclyzer.sh" ]
