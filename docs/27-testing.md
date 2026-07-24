# Axiom OS — Testing

## Test Suites

### Sprint 2 Validation Suite
`python3 backend/_sprint2_validation.py`

110 checks covering: bootstrap, executive board, registry loading, agents & capabilities, memory retrieval, event propagation, workflow lifecycle, dispatcher & retry, approval manager, health monitor, scheduler, recovery manager, intelligence engine, learning engine, runtime start/stop.

### Sprint 2 Stress & Recovery Tests
`python3 backend/_sprint2_stress_tests.py`

28 checks covering: failure injection, recovery from persisted state, memory consistency, event replay, capability resolution, dispatcher load testing, learning score consistency, executive autonomy.

### Sprint 1 Audit
`python3 backend/_sprint1_audit.py`

Completeness audit for Sprint 1 components.

## Running Tests

```bash
cd backend

# Full validation
python3 _sprint2_validation.py

# Stress tests
python3 _sprint2_stress_tests.py
```

## Test Architecture

Tests import `AxiomRuntime` directly and manipulate it via its public API. The runtime is started once, all tests run against the initialized system, then shutdown cleanly.

## Expected Results

- Validation: 110/110 (100%)
- Stress: 28/28 (100%)