#!/usr/bin/env bash

if [ "$1" = "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  echo "USAGE"
  echo ""
  echo "  ./do COMMAND"
  echo ""
  echo "COMMAND"
  echo ""
  echo "  shell                opens a shell inside the docker container with"
  echo "                       gcc, qemu, python3.12, and vim installed and"
  echo "                       the project directory mounted as a volume"
  echo ""
  echo "  compile PATH [ARGS]  compiles python file PATH to tmp directory in docker"
  echo "                       container. Optionally, pass additional command line"
  echo "                       arguments ARGS to your compiler.py"
  echo ""
  echo "  run PATH [ARGS]      like 'compile', but runs the generated file with"
  echo "                       qemu after compilation"
  echo ""
  echo "  test                 runs all tests in docker container"
  echo ""
  echo "  docker-rebuild       rebuilds the docker image (in case the Dockerfile"
  echo "                       has changed)"
  echo ""
  echo "  clean                clears tmp directory"
  exit 1
fi

WORK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
IMAGE_NAME="cc-riscv"

if ! command -v docker &> /dev/null; then
  echo "docker not installed, follow the installation instructions from the website: https://docs.docker.com/engine/install/"
  exit 1
fi

function ensure_docker_image {
  if ! sudo docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "docker image not found! building the image.."
    sudo docker build -t "$IMAGE_NAME" "$WORK_DIR"
  fi
}

if [ "$1" = "shell" ]; then
  ensure_docker_image
  sudo docker run -e "PYTHONHASHSEED=1" -it --rm -v "$WORK_DIR:/cc" -w /cc -u "$(id -u):$(id -g)" "$IMAGE_NAME" bash
elif [ "$1" = "compile" ]; then
  ensure_docker_image
  FILE_NAME="$(basename "$2" .py)"
  mkdir -p "$WORK_DIR/tmp"
  sudo docker run -e "PYTHONHASHSEED=1" -it --rm -v "$WORK_DIR:/cc" -w /cc -u "$(id -u):$(id -g)" "$IMAGE_NAME" bash -c \
    "python3.12 src/compiler.py -i \"$2\" -o \"tmp/$FILE_NAME.S\" ${@:3}"
elif [ "$1" = "run" ]; then
  ensure_docker_image
  FILE_NAME="$(basename "$2" .py)"
  mkdir -p "$WORK_DIR/tmp"
  sudo docker run -e "PYTHONHASHSEED=1" -it --rm -v "$WORK_DIR:/cc" -w /cc -u "$(id -u):$(id -g)" "$IMAGE_NAME" bash -c \
    "python3.12 \"src/compiler.py\" -i \"$2\" -o \"tmp/$FILE_NAME.S\" ${@:3}  
     riscv64-linux-gnu-gcc -static \"/cc/tmp/$FILE_NAME.S\" \"runtime/runtime.c\" -o \"tmp/$FILE_NAME\" 
     qemu-riscv64-static \"tmp/$FILE_NAME\""
elif [ "$1" = "test" ]; then
  ensure_docker_image
  sudo docker run -e "PYTHONHASHSEED=1" -it --rm -v "$WORK_DIR:/cc" -w /cc -u "$(id -u):$(id -g)" "$IMAGE_NAME" bash -c \
    "python3.12 tests/test.py ${@:2}"
elif [ "$1" = "docker-rebuild" ]; then
  echo "Rebuilding the docker image..."
  sudo docker build -t "$IMAGE_NAME" "$WORK_DIR"
elif [ "$1" = "clean" ]; then
   rm -rf "$WORK_DIR/tmp/"
else
  echo "Invalid command line arguments. Run with --help for documentation."
  exit 1
fi
