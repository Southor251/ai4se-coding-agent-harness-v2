.PHONY: test lint clean web demo

test:
	python -m pytest tests/ -v --tb=short

lint:
	python -m ruff check src/ tests/ demo/

clean:
	rm -rf .harness/trace/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/

web:
	streamlit run src/agent_harness/web/theater.py

demo:
	python -m demo.demo_guardrail
	python -m demo.demo_feedback
	python -m demo.demo_hitl_write
	python -m demo.demo_scope
