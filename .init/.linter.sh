#!/bin/bash
cd /home/kavia/workspace/code-generation/advanced-tic-tac-toe-platform-49128-49137/tic_tac_toe_api
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

