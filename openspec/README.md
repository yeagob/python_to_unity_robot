# OpenSpec: Specification-Driven Development

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) methodology for AI-assisted development. OpenSpec ensures that humans and AI agents agree on specifications before writing code, eliminating ambiguity and improving collaboration.

## Directory Structure

```
openspec/
├── README.md           # This file
├── specs/              # Source of truth - current specifications
│   ├── system.md       # Core system specification
│   ├── robot-interface.md  # LLM-Robot control interface
│   ├── chess-system.md     # Chess playing system
│   └── communication.md    # Python-Unity protocol
└── changes/            # Proposed changes (pending review)
    └── [change-folders]/
```

## Workflow

### 1. Proposing Changes

When proposing a new feature or modification:

1. Create a new folder in `changes/` with a descriptive name:
   ```
   changes/add-vision-system/
   ```

2. Inside the folder, create:
   - `proposal.md` - Justification and context for the change
   - `tasks.md` - Implementation checklist
   - `specs/` - Delta specifications (changes to existing specs)
   - `design.md` - Technical design decisions (optional)

### 2. Reviewing Changes

- Review the proposal and discuss with collaborators
- Iterate on the specifications until consensus is reached
- All requirements should be clear and testable

### 3. Implementing Changes

- Use the tasks.md as an implementation checklist
- Each task should reference specific requirements
- Mark tasks complete as implementation progresses

### 4. Archiving Changes

Once implementation is complete and verified:

1. Merge delta specs into the base `specs/` folder
2. Move the change folder to an archive (or delete)
3. Update version numbers in affected specifications

## Specification Format

### Requirements

```markdown
### Requirement: [ID] - [Name]
The system SHALL/MUST [behavior description]

#### Scenario: [Scenario Name]
- WHEN [condition]
- THEN [expected result]
- AND [additional expectations]
```

### Keywords

- **SHALL/MUST**: Mandatory requirement
- **SHOULD**: Recommended but not mandatory
- **MAY**: Optional feature
- **WHEN**: Trigger condition for a scenario
- **THEN**: Expected outcome
- **AND**: Additional conditions or outcomes

### Delta Specifications

When modifying existing specs, use these markers:

```markdown
## ADDED Requirements
[New requirements go here]

## MODIFIED Requirements
[Changed requirements with before/after]

## REMOVED Requirements
[Requirements being removed with justification]
```

## Current Specifications

| Spec | Description | Status |
|------|-------------|--------|
| [system.md](specs/system.md) | Core simulation system | Active |
| [robot-interface.md](specs/robot-interface.md) | LLM robot control API | Active |
| [chess-system.md](specs/chess-system.md) | Chess playing robot | Active |
| [communication.md](specs/communication.md) | Python-Unity protocol | Active |

## Benefits

1. **Clear Requirements**: Everyone understands what needs to be built
2. **Reduced Ambiguity**: Specifications live in files, not chat history
3. **Testable Scenarios**: Each requirement has verifiable scenarios
4. **Change Tracking**: All modifications go through the proposal process
5. **AI Collaboration**: LLMs can reference specs to understand context

## Example: Adding a New Feature

```bash
# 1. Create change folder
mkdir -p openspec/changes/add-camera-system

# 2. Create proposal
cat > openspec/changes/add-camera-system/proposal.md << 'EOF'
# Proposal: Camera Vision System

## Summary
Add a camera vision system to enable the robot to perceive its environment.

## Motivation
Currently the robot operates "blind" - it can only move to programmed positions.
Adding vision would enable adaptive behavior and object detection.

## Scope
- New camera component in Unity
- Image capture and streaming to Python
- Basic object detection interface
EOF

# 3. Create tasks
cat > openspec/changes/add-camera-system/tasks.md << 'EOF'
# Implementation Tasks

- [ ] VISION-001: Add Unity camera component
- [ ] VISION-002: Implement image capture
- [ ] VISION-003: Add streaming protocol to communication.md
- [ ] VISION-004: Create Python client for receiving images
- [ ] VISION-005: Write tests for camera functionality
EOF
```

## Contributing

1. Always create a change proposal before implementing significant features
2. Follow the requirement format for new specifications
3. Include scenarios for all requirements
4. Update version numbers when specs change
5. Archive completed changes appropriately
