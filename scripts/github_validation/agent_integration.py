"""
Agent System Integration

Optional integration with the agent system for enhanced validation
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AgentIntegration:
    """Optional agent system integration"""
    
    def __init__(self):
        """Initialize agent integration"""
        self.validation_agent = None
        self.quality_agent = None
        self._load_agents()
    
    def _load_agents(self):
        """Try to load agent system components"""
        try:
            from agents.validation_agent import ValidationAgent
            self.validation_agent = ValidationAgent(agent_id='github_validation')
            logger.info("ValidationAgent loaded successfully")
        except ImportError:
            logger.debug("ValidationAgent not available")
        except Exception as e:
            logger.warning(f"Error loading ValidationAgent: {e}")
        
        try:
            from agents.quality_assurance_agent import QualityAssuranceAgent
            self.quality_agent = QualityAssuranceAgent(agent_id='github_qa')
            logger.info("QualityAssuranceAgent loaded successfully")
        except ImportError:
            logger.debug("QualityAssuranceAgent not available")
        except Exception as e:
            logger.warning(f"Error loading QualityAssuranceAgent: {e}")
    
    def is_available(self) -> bool:
        """Check if agent system is available"""
        return self.validation_agent is not None or self.quality_agent is not None
    
    def run_agent_validation(self, validation_type: str = 'all') -> Dict[str, Any]:
        """Run validation using agent system if available"""
        if not self.is_available():
            return {
                'success': True,
                'skipped': True,
                'message': 'Agent system not available'
            }
        
        results = {
            'success': True,
            'agent_results': {}
        }
        
        # Use ValidationAgent if available
        if self.validation_agent:
            try:
                agent_result = self.validation_agent._execute_action(
                    action='validate_import_integrity',
                    parameters={},
                    user_context={'source': 'github_cmd'}
                )
                results['agent_results']['validation'] = agent_result
            except Exception as e:
                logger.warning(f"Error running ValidationAgent: {e}")
                results['agent_results']['validation'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Use QualityAssuranceAgent if available
        if self.quality_agent:
            try:
                agent_result = self.quality_agent._execute_action(
                    action='cfbd_health_check',
                    parameters={},
                    user_context={'source': 'github_cmd'}
                )
                results['agent_results']['quality'] = agent_result
            except Exception as e:
                logger.warning(f"Error running QualityAssuranceAgent: {e}")
                results['agent_results']['quality'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results

