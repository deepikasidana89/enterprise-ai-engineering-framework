# Rules

EARF Phase 2 stores declarative rule definitions as YAML files in this directory.

Rules are definitions only. They are not executed against repository evidence in Phase 2.

## Schema

Each file must define a top-level `rules` list.

```yaml
rules:
	- id: GOV-001
		title: AI system ownership is documented
		description: The repository identifies an accountable AI system owner.
		category: governance
		severity: high
		version: "1.0"
		enabled: true
		applicability:
			always: true
		rationale: Clear ownership improves accountability.
		recommendation: Document the owner and escalation path.
		tags: [governance, ownership]
		references: []
		evidence_requirements:
			any:
				- evidence_type: file
					identifiers: [CODEOWNERS, OWNERS]
		metadata: {}
```

Required fields:

- `id`, `title`, `description`, `category`, `severity`

Rule ID format:

- `^[A-Z]{3}-\d{3}$` (examples: `GOV-001`, `SEC-002`, `OBS-010`)

Severity values (case-insensitive in YAML):

- `critical`, `high`, `medium`, `low`, `info`

## Validate Rules

Validate all rules:

```bash
earf rules validate
```

Validate a custom path:

```bash
earf rules validate --path ./custom-rules
```
