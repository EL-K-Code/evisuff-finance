.PHONY: test validate smoke audit paper clean-paper workflow-test workflow-pilot experiment-test empirical-dry-run real-case-test real-case-validate privacy-test provider-test prepare-real-run run-real-models

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
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_enterprise_workflow.py' -v

workflow-pilot:
	PYTHONPATH=src python -m evisuff.workflow_cli synthetic-pilot data/ipo_workflow_pilot/spec.json --runs-dir results/ipo_pilot_runs --output results/ipo_workflow_pilot.json

experiment-test:
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_experiment_runner.py' -v

real-case-test:
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_real_cases.py' -v

privacy-test:
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_backend_privacy.py' -v

provider-test:
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_anthropic_backend.py' -v
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_prepare_real_run.py' -v
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_experiment_env.py' -v

real-case-validate:
	PYTHONPATH=src python -m evisuff.real_cases_cli data/ipo_real_cases/index.json --output results/real_ipo_case_validation.json

empirical-dry-run:
	PYTHONPATH=src python -m evisuff.experiment_cli run configs/ipo_empirical_dry_run.json --overwrite

prepare-real-run:
	python tools/prepare_real_run.py --env .env --output configs/ipo_empirical.local.json

run-real-models:
	PYTHONPATH=src python -m evisuff.experiment_cli run configs/ipo_empirical.local.json --env-file .env
