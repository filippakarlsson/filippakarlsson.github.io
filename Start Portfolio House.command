#!/bin/zsh

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR" || exit 1

if [[ ! -d node_modules ]]; then
  npm install || exit 1
fi

npm run dev -- --open
