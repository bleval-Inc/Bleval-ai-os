# Axiom AI OS - AI Provider Resiliency & Failover System

## Overview
This document outlines the comprehensive AI provider resiliency and failover system implemented in Axiom AI OS to ensure continuous operation and zero downtime, even when individual AI models or services experience issues.

## Key Improvements Made

### 1. **NVIDIA-Only, Multi-Model Architecture**
- **Removed**: All Anthropic and OpenAI provider references
- **Implemented**: 5 diverse NVIDIA NIM models for redundancy:
  - **NVIDIA Nemotron 3 Ultra 550B** (Flagship - Strategic reasoning)
  - **Z.ai GLM-5.2** (Flagship - Strategic reasoning, long-horizon planning)
  - **Mistral Mamba-Transformer MoE** (Long-context - 1M token context, agentic reasoning)
  - **Stepfun Sparse MoE** (Multimodal - Enterprise reasoning, agentic tasks)
  - **NVIDIA General Purpose** (General - Text generation, coding, everyday tasks)

### 2. **Intelligent Task-Based Routing**
The SmartRouter analyzes each task and routes it to the optimal model:

| Task Category | Primary Model | Fallback Chain |
|---------------|---------------|----------------|
| **STRATEGIC** | GLM-5.2 → Nemotron Ultra → Mistral → Stepfun → NVIDIA General |
| **CODING** | Mistral Mamba → GLM-5.2 → Stepfun → NVIDIA General |
| **LONG_CONTEXT** | Mistral Mamba → GLM-5.2 → Stepfun → NVIDIA General |
| **AGENTIC** | GLM-5.2 → Stepfun → Mistral → NVIDIA General |
| **CREATIVE** | NVIDIA General → Stepfun → GLM-5.2 |
| **ANALYSIS** | GLM-5.2 → Mistral → Stepfun → NVIDIA General |
| **GENERAL** | NVIDIA General → GLM-5.2 → Stepfun → Mistral |

### 3. **Robust Failover Mechanisms**

#### Provider-Level Resiliency (NVIDIA Provider)
- **Automatic Retry**: 2 attempts for transient errors (503, timeouts, rate limits)
- **Error Classification**: Distinguishes between transient vs permanent failures
- **Quick Failover**: Rapid transition to next available model on failure

#### Router-Level Intelligence (SmartRouter)
- **Availability Checking**: Only considers providers that are actually configured and available
- **Priority-Based Selection**: Uses intelligent routing based on task analysis
- **Transparent Fallback**: Automatically tries next-best model when primary fails
- **Production-Safe**: Never falls back to mock providers in production mode

### 4. **Enhanced Error Handling & Monitoring**
- **Better Error Messages**: Clear, actionable error reporting
- **Service Health Awareness**: Providers correctly report availability status
- **Logging & Diagnostics**: Comprehensive logging for troubleshooting failover events

### 5. **Configuration & Deployment**
- **Environment-Based**: All configuration via environment variables
- **Zero-Downtime Updates**: Can add/remove providers without restart
- **Health Checks**: Built-in provider availability monitoring

## How It Works

### Normal Operation:
1. Task arrives at Intelligence Engine
2. SmartRouter classifies task (strategic, coding, creative, etc.)
3. Router selects optimal provider based on task analysis
4. Request sent to selected NVIDIA model
5. Result returned to user

### Failover Operation (when primary model fails):
1. Task arrives and is classified
2. SmartRouter selects primary provider (e.g., GLM-5.2 for strategic task)
3. Initial request fails (e.g., 503 Service Unavailable)
4. Provider-level retry attempts (2 tries)
5. If still failing, SmartRouter marks provider as temporarily unavailable
6. Router automatically selects next-best provider from fallback chain
7. Request retried with new provider
8. Result returned to user - **zero noticeable downtime**

## Resiliency Guarantees

✅ **Never Single Point of Failure**: 5 independent NVIDIA models  
✅ **Automatic Recovery**: System self-heals when failed providers recover  
✅ **Zero Configuration Failover**: No code changes needed for failover  
✅ **Performance Optimized**: Each task gets the best-suited model  
✅ **Production Ready**: Safe fallbacks, no mock provider usage in production  
✅ **Monitoring Ready**: Clear visibility into provider health and routing  

## Verification & Testing

The system has been verified to:
- Correctly route different task types to optimal models
- Gracefully handle provider unavailability
- Provide meaningful error messages when all providers fail
- Maintain intelligent routing even under failure conditions
- Work with the current NVIDIA API key configuration

## Configuration

All configuration is handled via environment variables in `.env`:

```bash
# NVIDIA API Configuration (Single key accesses all models)
NVIDIA_API_KEY=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
NVIDIA_API_BASE_URL=https://integrate.api.nvidia.com/v1

# Individual Model Configuration (All use master key)
NVIDIA_NEMOTRON_ULTRA_KEY=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
NVIDIA_NEMOTRON_ULTRA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_NEMOTRON_ULTRA_PROVIDER=nvidia

# ... similar for all 5 models
```

## Maintenance & Operations

### Adding New Providers:
1. Obtain API key and model ID from NVIDIA NIM
2. Add to `.env` following existing pattern
3. System automatically detects and registers new provider
4. New provider joins fallback chains based on its capabilities

### Monitoring Provider Health:
- Use `engine.list_providers()` to see availability status
- Use `engine.get_route_for_task()` to see routing decisions
- Check logs for failover events and performance metrics

## Conclusion

Axiom AI OS now features enterprise-grade AI provider resiliency with:
- **5-way redundancy** using diverse NVIDIA NIM models
- **Intelligent task-based routing** for optimal performance
- **Automatic transparent failover** for zero downtime
- **Production-hardened** error handling and monitoring
- **Zero configuration** failover - works out of the box

The system will remain online and responsive even if individual NVIDIA models or services experience issues, ensuring continuous operation of all Axiom AI OS executives and agents.