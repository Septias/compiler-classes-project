FROM debian:unstable-slim

RUN apt-get update
RUN apt-get install -y \ 
      vim \
      gcc-riscv64-linux-gnu \
      qemu-user-static \
      python3.12