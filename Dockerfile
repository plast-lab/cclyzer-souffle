FROM ubuntu:24.04

# Pinned so that the image can be rebuilt the same way later.
# LLVM_VERSION must be at least LLVM_MIN_MAJOR in src/common.mk.
ARG LLVM_VERSION=22
ARG SOUFFLE_VERSION=2.5

ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC
WORKDIR /workdir

RUN apt-get -y update && apt-get -y install \
        bison build-essential ca-certificates cmake flex g++ git gnupg \
        libffi-dev libncurses-dev libsqlite3-dev make mcpp python3 \
        python3-dev sqlite3 wget zlib1g-dev \
        libboost-dev libboost-filesystem-dev libboost-program-options-dev \
        libboost-python-dev

# Soufflé with 64-bit domains: the default 32-bit build cannot load facts
# that contain LLVM's ~0U sentinel (4294967295).
RUN git clone --depth 1 --branch ${SOUFFLE_VERSION} https://github.com/souffle-lang/souffle.git && \
    cmake -S souffle -B souffle/build -DCMAKE_INSTALL_PREFIX=/usr \
          -DSOUFFLE_DOMAIN_64BIT=ON -DSOUFFLE_ENABLE_TESTING=OFF && \
    cmake --build souffle/build -j8 --target install && \
    rm -r souffle

# LLVM from apt.llvm.org, since Ubuntu's own packages lag behind.
RUN wget -qO /etc/apt/trusted.gpg.d/apt.llvm.org.asc https://apt.llvm.org/llvm-snapshot.gpg.key && \
    echo "deb http://apt.llvm.org/noble/ llvm-toolchain-noble-${LLVM_VERSION} main" \
        > /etc/apt/sources.list.d/llvm.list && \
    apt-get -y update && apt-get -y install \
        clang-${LLVM_VERSION} llvm-${LLVM_VERSION}-dev libclang-${LLVM_VERSION}-dev

ADD . cclyzer-souffle
RUN cd cclyzer-souffle && \
    make -j8 LLVM_CONFIG=llvm-config-${LLVM_VERSION}

ENTRYPOINT [ "/workdir/cclyzer-souffle/cclyzer.sh" ]
