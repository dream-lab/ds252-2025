#!/usr/bin/env bash
set -euo pipefail
JM_VERSION="${JM_VERSION:-5.6.3}"
INSTALL_DIR="$HOME/jmeter"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if ! command -v java >/dev/null 2>&1; then
  if [[ "$(uname)" == "Darwin" ]]; then
    brew install openjdk || true
  else
    sudo apt-get update -y && sudo apt-get install -y openjdk-11-jre || sudo apt-get install -y default-jre
  fi
fi

cd "$INSTALL_DIR"
curl -L -o apache-jmeter.tgz "https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JM_VERSION}.tgz"
tar xf apache-jmeter.tgz
ln -sf "$INSTALL_DIR/apache-jmeter-${JM_VERSION}/bin/jmeter" "$BIN_DIR/jmeter"

echo 'Add to your shell rc if needed: export PATH="$HOME/.local/bin:$PATH"'
echo "Then run: jmeter -v"
