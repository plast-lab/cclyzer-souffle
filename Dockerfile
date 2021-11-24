FROM ubuntu:latest

WORKDIR /workdir
RUN apt-get -y update

# Build and install souffle
RUN DEBIAN_FRONTEND=noninteractive TZ=Europe/Rome apt-get -y install autoconf automake bison build-essential clang doxygen flex g++ git libffi-dev libncurses5-dev libtool libsqlite3-dev make mcpp python sqlite zlib1g-dev cmake
RUN git clone https://github.com/souffle-lang/souffle.git
RUN cd souffle && \
    cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr && \
    cmake --build build -j8 --target install

# Build and install cclyzer
RUN DEBIAN_FRONTEND=noninteractive TZ=Europe/Rome apt-get -y install llvm
RUN DEBIAN_FRONTEND=noninteractive TZ=Europe/Rome apt-get -y install libclang-dev python-dev build-essential libboost-dev libboost-filesystem-dev libboost-program-options-dev libboost-python-dev
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python38.so /usr/lib/x86_64-linux-gnu/libboost_python.so

ADD . cclyzer-souffle
RUN cd cclyzer-souffle && \
    make -j

ENTRYPOINT [ "/workdir/cclyzer-souffle/cclyzer.sh" ]
