.PHONY: test validate smoke audit paper clean-paper

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
