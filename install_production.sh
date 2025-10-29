#!/bin/bash

# DEPRECATED: movido para scripts/install_production.sh
# Shim que executa o script novo em scripts/ para compatibilidade.

exec "$(dirname "$0")/scripts/install_production.sh" "$@"
