from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine

print('Testing with environment variable set...')
print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')

engine = IntelligenceEngine()
providers = engine.router.get_available_providers()

print(f'Number of providers registered: {len(providers)}')
gateway_providers = [p for p in providers if p['name'] == 'external-gateway']
print(f'Gateway providers found: {len(gateway_providers)}')

if gateway_providers:
    provider = gateway_providers[0]
    print(f'Gateway provider name: {provider["name"]}')
    print(f'Gateway provider available: {provider["available"]}')
