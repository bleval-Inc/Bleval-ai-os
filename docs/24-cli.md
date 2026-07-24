# Axiom OS — CLI

## Overview

The CLI provides terminal access to runtime operations through a Typer-based command-line interface.

## Usage

```bash
python -m axiom.cli.main [command]
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Runtime status | `python -m axiom.cli.main status` |
| `workflows` | List workflow definitions | `python -m axiom.cli.main workflows` |
| `launch <id>` | Launch workflow | `python -m axiom.cli.main launch sales/prospect-research` |
| `instances` | List instances | `python -m axiom.cli.main instances` |
| `advance <id>` | Advance instance | `python -m axiom.cli.main advance <instance_id>` |
| `agents` | List agents | `python -m axiom.cli.main agents` |
| `organisations` | List organizations | `python -m axiom.cli.main organisations` |
| `capabilities` | List capabilities | `python -m axiom.cli.main capabilities` |
| `events` | List event types | `python -m axiom.cli.main events` |
| `memory <agent_id>` | Agent memory context | `python -m axiom.cli.main memory jenson` |
| `health` | System health | `python -m axiom.cli.main health` |

## Implementation

CLI is implemented in `backend/axiom/cli/main.py` using the Typer library. It creates a runtime instance and calls the same engine methods as the API.