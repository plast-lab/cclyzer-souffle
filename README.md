# CClyzer

A tool for analyzing LLVM bitcode (generated either by C, C++ or Rust) using
Datalog.

Soufflé, an open-source Datalog engine for program analysis, is the Datalog
engine of choice.

Set Up
------

### Install the Soufflé engine

The Soufflé Datalog engine needs to be installed. We recommend using the HEAD
commit (until at least a few much needed improvements of version 2 become stable)
by cloning the Soufflé GitHub [repo](https://github.com/souffle-lang/souffle)
and following the available
[instructions](https://souffle-lang.github.io/build) to build from source.

The latest development version of Soufflé can also be installed via the package
manager of certain distributions listed [here](https://souffle-lang.github.io/install).

### Install LLVM

The current version of cclyzer supports (in some cases partially) all versions
of LLVM starting from 3.7 and up to 10. LLVM can be built from source even
though this is not needed for newer Linux distributions, where installation via
the system's package manager should suffice.

#### Ubuntu 20.04

    apt install llvm
 
#### Fedora 32

    dnf install gcc-c++ llvm-devel
  
### Additional Libraries

You will also have to install the following packages:

#### Ubuntu 20.04

    apt install libclang-dev python-dev build-essential libboost-dev libboost-filesystem-dev libboost-program-options-dev libboost-python-dev

#### Fedora 32

    dnf install python-devel boost-python3-devel

Even though the necessary boost libraries are now available in your system, the
compiler might fail to locate and link against them when building cclyzer. Next,
we give one possible solution to this problem.

Locate the libboost libraries in your system by running:

    echo "$(ldconfig -p | grep libboost_python* | tr ' ' '\n' | grep /)"

The above command should print something along the following lines:

```
/usr/lib/libboost_python27.so.1.70.0
/usr/lib/libboost_python27.so
/usr/lib/x86_64-linux-gnu/libboost_python3-py36.so.1.65.1
/usr/lib/x86_64-linux-gnu/libboost_python3-py36.so
/usr/lib/x86_64-linux-gnu/libboost_python-py27.so.1.65.1
/usr/lib/x86_64-linux-gnu/libboost_python-py27.so
```

As a next step you need to select the most recent version of Python 3,
`/usr/lib/x86_64-linux-gnu/libboost_python3-py36.so.1.65.1` in our example,
and create a link to it in a directory you have write access such as
`$HOME/.local/lib`.

    mkdir -p $HOME/.local/lib
    ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py36.so.1.65.1 $HOME/.local/lib/libboost_python.so
 
Finally, append the following to `.bashrc` or `.bash_profile` to update the
`LIBRARY_PATH` and `LD_LIBRARY_PATH` environment variables. Do not forget to
`source .bashrc` or `source .bash_profile` afterwards.

    export LIBRARY_PATH="$HOME/.local/lib:$LIBRARY_PATH"
    export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"
    
Build
-----
    
In the base directory run:

    make

Run
---

The default way to run, using a context-insensitive analysis, is:

    ./cclyzer.sh -i <input_file>

To analyze a file with a specific analysis run:

    ./cclyzer.sh -a <analysis> -i <input_file>

where the available options for <analysis> are:

* context-insensitive
* 1-call-site-sensitive+heap
* 2-call-site-sensitive+heap

