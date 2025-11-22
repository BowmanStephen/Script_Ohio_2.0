# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with project decision documentation and architectural rationale.

## Decision Log Management

This directory maintains a comprehensive record of all significant project decisions, their rationale, alternatives considered, and expected impacts. This serves as the institutional memory and provides context for future decision-making.

### Key Decision Categories

- **`architecture_decisions.md`**: Technical architecture and system design decisions
- **scope_decisions.md`**: Project scope, feature inclusion/exclusion decisions
- `prioritization_decisions.md`: Feature prioritization and resource allocation decisions

## Decision Documentation Standards

### Required Elements for Each Decision
1. **Decision Title**: Clear, descriptive title
2. **Date**: When the decision was made
3. **Decision Maker(s)**: Who made the decision
4. **Problem Statement**: What problem or opportunity prompted the decision
5. **Alternatives Considered**: What other options were evaluated
6. **Decision**: What was decided
7. **Rationale**: Why this decision was made
8. **Expected Impact**: Anticipated consequences and benefits
9. **Implementation Notes**: How the decision will be implemented
10. **Review Date**: When the decision should be revisited

### Decision Classification
- **Strategic**: High-level project direction decisions
- **Architectural**: Technical design and infrastructure decisions
- **Scope**: Feature inclusion/exclusion decisions
- **Tactical**: Implementation approach decisions
- **Process**: Workflow and methodology decisions

## Usage Patterns

### For Understanding Project Context
1. **Start Here**: Review relevant decision logs when starting new work
2. **Architecture Context**: Check `architecture_decisions.md` for technical rationale
3. **Scope Understanding**: Review `scope_decisions.md` for project boundaries

### For Making New Decisions
1. **Research Past Decisions**: Check for similar previous decisions
2. **Follow Format**: Use established decision documentation format
3. **Consider Impact**: Document expected consequences and trade-offs

### For Problem Resolution
1. **Decision Context**: Review relevant decisions when troubleshooting issues
2. **Rationale Understanding**: Understand why decisions were made to avoid repeating mistakes
3. **Alternative Review**: Consider previously rejected alternatives when new information emerges

## Decision Review Process

### Regular Reviews
- **Monthly**: Review recent decisions for accuracy and continued relevance
- **Quarterly**: Strategic decision review and validation
- **Annually**: Comprehensive decision audit and lessons learned

### Decision Updates
- Document when decisions are modified or reversed
- Include new rationale for changes
- Cross-reference original decision
- Update expected impact based on actual outcomes

### Decision Reversal
- Clearly document when and why decisions are reversed
- Include lessons learned from the reversal
- Update related decisions that may be affected
- Communicate changes to relevant stakeholders

## Integration with Project Management

This decision log integrates with the broader project management system:

- **Current State**: Decisions reflected in implementation status
- **Roadmaps**: Decisions aligned with strategic roadmaps
- **Quality Assurance**: Quality-related decisions inform testing approaches
- **Risk Management**: Decisions document risk mitigation strategies

## File Organization

### Chronological Organization
- Maintain chronological order within each decision category
- Include date in decision titles for easy reference
- Create summary tables for quick decision lookup

### Cross-Referencing
- Cross-reference related decisions across categories
- Link decisions to implementation in code and documentation
- Reference decisions in project planning and status updates

### Decision Tagging
- Tag decisions by category (architecture, scope, etc.)
- Tag by impact level (high, medium, low)
- Tag by status (active, implemented, superseded, reversed)

## Access Guidelines

### Read Access
- All team members should read decisions relevant to their work
- Review decision logs before starting new features or changes
- Reference decisions when discussing project direction

### Write Access
- Document all significant project decisions promptly
- Use established format and include all required elements
- Review decisions with team before finalizing

### Decision Authority
- Technical decisions: Technical lead or architecture team
- Scope decisions: Product owner or project manager
- Strategic decisions: Project stakeholders and leadership team

---

**Decision Log Philosophy**: This directory ensures project decisions are transparent, well-documented, and accessible for future reference. Good decision documentation prevents repeated mistakes and provides context for continued project development.