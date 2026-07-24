# Axiom OS — Intelligence Engine

## Overview

The Intelligence Engine handles model routing, context assembly, and response generation. It supports multiple AI providers with automatic fallback.

## Providers

| Provider | Model | Use Case |
|----------|-------|----------|
| AnthropicProvider | Claude Opus | Complex reasoning, strategic decisions |
| AnthropicFastProvider | Claude Sonnet/Haiku | Fast responses, simpler tasks |
| OpenAIProvider | GPT-4o | General purpose |
| OpenAIFastProvider | GPT-4o-mini | High-throughput, low-cost |
| MockProvider | — | Development/testing (no API key needed) |

## Provider Router

Routes by complexity:
- **Simple**: Fast provider (Haiku / 4o-mini)
- **Normal**: Standard provider (Sonnet / 4o)
- **Complex**: Powerful provider
- **Strategic**: Anthropic strategic

## Context Assembly

`ContextBuilder` assembles prompts from:
1. Instructions (agent identity)
2. Memory context (layered memory)
3. Available tools
4. Task description

## Key Operations

- `generate(agent_id, task_description, org_id)` — Full generation with context
- `assemble_prompt(agent_id, task_description, org_id)` — Build prompt string
- `build_system_prompt(agent_id, org_id)` — Build system prompt
- `list_providers()` — List registered providers

## Fallback

If no API keys are set, the system falls back to MockProvider, which returns canned responses for development and testing.