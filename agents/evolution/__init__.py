#!/usr/bin/env python3
"""
Project Sentinel: Evolution Module

This module contains the Agent Speciation Engine - the heart of Project Sentinel's
ability to create evolving, specialized agent species for football analytics.

The evolution system enables agents to:
- Evolve and specialize through genetic algorithms
- Cross-breed to create hybrid capabilities
- Adapt to specific analytical domains
- Develop emergent behaviors beyond original programming
- Form symbiotic relationships within the ecosystem

Author: Claude Code Assistant
Created: 2025-11-12
Purpose: Revolutionary agent evolution and speciation system
"""

from .agent_genome import AgentGenome
from .evolution_metrics import EvolutionMetrics
from .genetic_algorithms import GeneticAlgorithmFramework
from .speciation_engine import AgentSpeciation
from .species_registry import SpeciesRegistry

__version__ = "1.0.0"
__status__ = "ACTIVE TRANSFORMATION"

# Core evolution components for creating AI species
__all__ = [
    "AgentSpeciation",  # Main speciation engine
    "GeneticAlgorithmFramework",  # Genetic algorithm implementation
    "AgentGenome",  # Agent genetic encoding
    "SpeciesRegistry",  # Species management system
    "EvolutionMetrics",  # Evolution progress tracking
]

print("🧬 Project Sentinel Evolution Module Initialized")
print("🏈 Creating AI species specialized in football analytics...")
