FROM ubuntu:22.04

RUN dpkg --add-architecture i386

RUN apt update && apt install -y \
    build-essential \
    gcc-multilib \
    gdb \
    nasm \
    python3 \
    python3-pip \
    vim \
    git \
    binutils \
    checksec

WORKDIR /workspace