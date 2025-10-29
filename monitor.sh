#!/bin/bash

# DEPRECATED: movido para scripts/monitor.sh
# Shim que executa o script novo em scripts/ para compatibilidade.

exec "$(dirname "$0")/scripts/monitor.sh" "$@"