"""
Register File Organization and Validation Agents with the Agent Factory

This script registers our new specialized agents with the existing AgentFactory
so they can be used by the AnalyticsOrchestrator and other system components.
"""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_organization_agents():
    """Register the file organization and validation agents with the factory"""

    try:
        # Import the factory and our agents
        from agents.core.agent_framework import AgentFactory
        from agents.file_organization_agent import FileOrganizationAgent, create_file_organization_agent
        from agents.validation_agent import ValidationAgent, create_validation_agent

        # Initialize the factory
        factory = AgentFactory()
        logger.info("Agent Factory initialized successfully")

        # Register our new agents
        factory.register_agent_class(FileOrganizationAgent, 'file_organization')
        logger.info("✅ Registered FileOrganizationAgent as 'file_organization'")

        factory.register_agent_class(ValidationAgent, 'validation')
        logger.info("✅ Registered ValidationAgent as 'validation'")

        # Test creating agent instances
        try:
            file_org_agent = factory.create_agent('file_organization', 'test_file_org_001')
            logger.info(f"✅ Created File Organization Agent: {file_org_agent.agent_id}")
            logger.info(f"   Capabilities: {[cap.name for cap in file_org_agent.capabilities]}")

            validation_agent = factory.create_agent('validation', 'test_validation_001')
            logger.info(f"✅ Created Validation Agent: {validation_agent.agent_id}")
            logger.info(f"   Capabilities: {[cap.name for cap in validation_agent.capabilities]}")

        except Exception as e:
            logger.error(f"❌ Failed to create agent instances: {e}")
            return False

        # Show all registered agents
        logger.info("📋 All registered agents:")
        for agent_type, agent_class in factory.agent_registry.items():
            logger.info(f"   - {agent_type}: {agent_class.__name__}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to register agents: {e}")
        return False


def test_agent_functionality():
    """Test basic functionality of our registered agents"""

    logger.info("🧪 Testing agent functionality...")

    try:
        from agents.core.agent_framework import AgentFactory
        factory = AgentFactory()

        # Test file organization agent
        logger.info("Testing File Organization Agent...")
        file_org_agent = factory.create_agent('file_organization', 'test_file_org')

        result = file_org_agent.process_request("classify_root_files", {})
        if result['status'] == 'success':
            logger.info(f"✅ File classification works: {result['result']['total_files']} files found")
        else:
            logger.error(f"❌ File classification failed: {result.get('error', 'Unknown error')}")

        # Test validation agent
        logger.info("Testing Validation Agent...")
        validation_agent = factory.create_agent('validation', 'test_validation')

        result = validation_agent.process_request("validate_import_integrity", {})
        if result['status'] == 'success':
            success_rate = result['result']['import_success_rate']
            logger.info(f"✅ Import validation works: {success_rate:.1%} success rate")
        else:
            logger.error(f"❌ Import validation failed: {result.get('error', 'Unknown error')}")

        return True

    except Exception as e:
        logger.error(f"❌ Agent functionality test failed: {e}")
        return False


def main():
    """Main registration and testing function"""

    logger.info("🚀 Starting agent registration process...")
    logger.info("=" * 60)

    # Step 1: Register agents
    if register_organization_agents():
        logger.info("✅ Agent registration completed successfully")
    else:
        logger.error("❌ Agent registration failed")
        return False

    logger.info("=" * 60)

    # Step 2: Test functionality
    if test_agent_functionality():
        logger.info("✅ Agent functionality tests passed")
    else:
        logger.error("❌ Agent functionality tests failed")
        return False

    logger.info("=" * 60)
    logger.info("🎉 All agents registered and tested successfully!")
    logger.info("The agents are now ready to be used by the AnalyticsOrchestrator.")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)