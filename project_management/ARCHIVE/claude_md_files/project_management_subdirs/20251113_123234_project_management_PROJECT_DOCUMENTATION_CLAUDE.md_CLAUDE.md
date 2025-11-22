# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with project documentation and user guides.

## Project Documentation Management

This directory contains comprehensive documentation for Script Ohio 2.0 project, serving both technical audiences and end users. This is the primary source of truth for project knowledge transfer and user guidance.

### Documentation Categories

- **User Guides**: Step-by-step instructions for using system
- **Technical Documentation**: System architecture, APIs, and development guides
- **Quick Start Guides**: Rapid onboarding documentation for different user types
- **Troubleshooting Guides**: Common issues and their solutions
- **Update Guides**: Documentation for major updates and migrations

### Key Documentation Files

#### 2025 Season Documentation
- **`2025_UPDATE_GUIDE.md`**: Comprehensive guide for 2025 data integration
- **`QUICK_START_2025.md`**: Fast start guide for 2025 season data
- **`TROUBLESHOOTING_2025.md`**: Specific troubleshooting for 2025 implementation
- **`2025_TESTING_REPORT.md`**: Quality assurance and testing results

#### System Documentation
- **`MODEL_USAGE_GUIDE.md`**: How to use trained ML models
- **`EXECUTIVE_SUMMARY_2025.md`**: High-level project overview and status
- **`DOCUMENTATION_MISSION_COMPLETE.md`**: Documentation completion status
- **`AGENT_ARCHITECTURE_GUIDE.md`**: **Complete intelligent agent system architecture and implementation guide (production-ready, Grade A+ quality)**

#### Quality and Fix Documentation
- **`FIXES_APPLIED_REPORT.md`**: Record of all fixes applied to system
- **`QUICK_START_FIXED.md`**: Updated quick start guide after fixes

## Documentation Standards

### Document Structure
Each document should include:
1. **Title and Purpose**: Clear description of document content
2. **Target Audience**: Who this document is for
3. **Last Updated**: Date of last revision
4. **Table of Contents**: For documents longer than 5 pages
5. **Prerequisites**: What users need before starting
6. **Step-by-Step Instructions**: Clear, actionable steps
7. **Troubleshooting**: Common issues and solutions
8. **Related Documents**: Cross-references to related documentation

### Writing Guidelines
- Use clear, simple language appropriate for target audience
- Include code examples and screenshots where helpful
- Provide both conceptual explanations and practical instructions
- Use consistent formatting and terminology across documents
- Include examples and use cases to illustrate concepts

### Technical Documentation Standards
- Include code syntax highlighting
- Provide API endpoint documentation with examples
- Document system architecture with diagrams
- Include configuration examples and best practices
- Reference related code files and components

## Usage Patterns

### For New Users
1. **Start with Quick Start**: Use appropriate quick start guide based on user type
2. **Read User Guides**: Consult detailed user guides for specific features
3. **Check Troubleshooting**: Reference troubleshooting guides for issues

### For Developers
1. **System Overview**: Start with executive summary and architecture documentation
2. **Model Usage**: Consult model usage guide for ML implementation
3. **API Documentation**: Review technical documentation for integration details

### For System Administration
1. **Update Guides**: Use update guides for system maintenance and upgrades
2. **Troubleshooting**: Reference troubleshooting guides for system issues
3. **Quality Reports**: Review testing reports for system validation

## Document Maintenance

### Regular Updates
- **User Guides**: Update with feature changes and improvements
- **Technical Documentation**: Update with architecture changes and new APIs
- **Quick Start Guides**: Update for new user onboarding flows
- **Troubleshooting Guides**: Add new issues and solutions as they emerge

### Version Control
- Include version numbers for major documentation updates
- Maintain change logs for documentation revisions
- Archive old versions when significant updates are made
- Cross-reference related documentation versions

### Quality Assurance
- Review documentation for accuracy and clarity
- Test instructions to ensure they work as described
- Validate code examples and configuration snippets
- Ensure cross-references are accurate and up-to-date

## Document Types and Their Usage

### Quick Start Guides
- **Purpose**: Rapid onboarding for new users
- **Length**: 1-5 pages maximum
- **Content**: Essential steps to get started quickly
- **Audience**: New users, evaluators, demo purposes

### User Guides
- **Purpose**: Comprehensive feature documentation
- **Length**: 5-50 pages depending on complexity
- **Content**: Detailed feature explanations and instructions
- **Audience**: Regular users, power users

### Technical Documentation
- **Purpose**: System architecture and development guidance
- **Length**: 10-100 pages depending on scope
- **Content**: Technical specifications, APIs, code examples
- **Audience**: Developers, system administrators

### Troubleshooting Guides
- **Purpose**: Issue resolution and problem solving
- **Length**: 2-20 pages depending on scope
- **Content**: Common issues, error messages, solutions
- **Audience**: All users experiencing issues

## 🚀 Development Commands

### Accessing Documentation
```bash
# View comprehensive agent architecture guide (RECOMMENDED)
cat AGENT_ARCHITECTURE_GUIDE.md

# Quick start for 2025 season
cat QUICK_START_2025.md

# Troubleshooting guide
cat TROUBLESHOOTING_2025.md

# Model usage guidance
cat MODEL_USAGE_GUIDE.md
```

### Documentation Validation
```bash
# Check documentation completeness
python -c "
import os
docs = [f for f in os.listdir('.') if f.endswith('.md')]
print(f'Documentation files: {len(docs)}')
required_docs = ['AGENT_ARCHITECTURE_GUIDE.md', 'QUICK_START_2025.md', 'TROUBLESHOOTING_2025.md']
missing = [d for d in required_docs if d not in docs]
print(f'Missing required docs: {missing if missing else \"None\"}')
"
```

### System Status via Documentation
```bash
# Executive summary for high-level overview
cat EXECUTIVE_SUMMARY_2025.md

# Implementation status tracking
cat ../CURRENT_STATE/AGENT_IMPLEMENTATION_STATUS_2025.md

# Quality assurance results
cat ../QUALITY_ASSURANCE/FINAL_QUALITY_REPORT_2025.md
```

## Integration with Project Management

This documentation integrates with broader project management system:

- **Current State**: Documentation reflects current implementation status (production-ready as of November 10, 2025)
- **Decision Log**: Documentation incorporates architectural decisions
- **Quality Assurance**: Documentation includes testing and validation results (Grade A+ quality achieved)
- **Roadmaps**: Documentation aligned with feature roadmaps and timelines
- **🤖 Agent System**: Complete integration with agents/CLAUDE.md for comprehensive system documentation

## Access Guidelines

### Document Creation
- Use appropriate templates for consistency
- Include all required sections and elements
- Review for accuracy and completeness before publication
- Test all instructions and code examples

### Document Updates
- Update documentation when features or systems change
- Review and update troubleshooting guides with new issues
- Maintain version history for significant changes
- Communicate documentation updates to relevant stakeholders

### Document Access
- Organize documents by audience and purpose
- Provide clear navigation between related documents
- Ensure documents are accessible to target audiences
- Maintain document inventory and index

---

**Documentation Philosophy**: This directory provides comprehensive, accurate, and accessible documentation for all project stakeholders. Good documentation enables user success, reduces support burden, and facilitates knowledge transfer across the project team.