#!/usr/bin/env python3
"""Debug script to see exact category values."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.smart_router import SmartRouter, TaskCategory

def debug_routing():
    print('Debugging Router Categories')
    print('=' * 30)

    # Create intelligence engine
    engine = IntelligenceEngine()

    # Get the smart router
    router = engine.router

    # Test a simple general task
    general_task = "Hello, how are you today?"
    route_info = router.get_route_for_task(general_task)

    print(f'Task: "{general_task}"')
    print(f'Returned category: "{route_info["task_category"]}"')
    print(f'Category type: {type(route_info["task_category"])}')

    # Check enum values
    print(f'TaskCategory.GENERAL.value: {TaskCategory.GENERAL.value}')
    print(f'TaskCategory.GENERAL: {TaskCategory.GENERAL}')

    # Test classification directly
    from axiom.engine.smart_router import TaskClassifier
    classifier = TaskClassifier()
    profile = classifier.classify(general_task)
    print(f'Profile category: {profile.category}')
    print(f'Profile category.value: {profile.category.value}')

if __name__ == '__main__':
    debug_routing()