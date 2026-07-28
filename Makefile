.PHONY: test validate smoke audit paper clean-paper workflow-test workflow-pilot

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

validate:
	PYTHONPATH=src python -m evisuff.cli validate data/example_annotations.jsonl

smoke:
	PYTHONPATH=src python -m evisuff.cli smoke --output results/smoke_metrics.json

audit:
	@echo "Usage: python tools/audit_upstream.py /path/to/ipoagent --output results/upstream_repository_audit.json"

paper:
	$(MAKE) -C paper pdf

clean-paper:
	$(MAKE) -C paper clean

workflow-test:
	PYTHONPATH=src python -m unittest tests.test_enterprise_workflow -v

workflow-pilot:
	PYTHONPATH=src python -m evisuff.workflow_cli synthetic-pilot data/ipo_workflow_pilot/spec.json --runs-dir results/ipo_pilot_runs --output results/ipo_workflow_pilot.json
