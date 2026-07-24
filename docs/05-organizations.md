# Axiom OS — Organizations

## Overview

Three organizations are defined, each with its own executive, departments, and boundaries.

## Organization Definitions

### bleval (Jenson)
- **ID**: `bleval`
- **Executive**: jenson
- **Departments**: sales, marketing, development, operations, finance
- **Memory**: `memory/bleval/`

### hov — House of Valta (Valta Prime)
- **ID**: `hov`
- **Executive**: valta_prime
- **Departments**: brand, creative, research, content, growth, operations
- **Memory**: `memory/hov/`

### personal (Yamako)
- **ID**: `personal`
- **Executive**: yamako
- **Departments**: productivity, knowledge
- **Memory**: `memory/personal/`

## Organization Structure

Each organization is defined in `organizations/{org_id}/organization.yaml`:
- Identity metadata (name, description, founder)
- Executive assignment
- Department definitions with managers
- Boundaries (can_control / cannot_control)
- Enabled tools
- Memory access levels

## API Endpoints
- `GET /api/v1/organisations` — List all organizations
- `GET /api/v1/organisations/{org_id}` — Get organization detail
- `GET /api/v1/organisations/{org_id}/departments` — List departments