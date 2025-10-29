#!/bin/bash

# DEPRECATED: movido para scripts/install_complete.sh
# Shim que executa o script novo em scripts/ para compatibilidade.

exec "$(dirname "$0")/scripts/install_complete.sh" "$@"