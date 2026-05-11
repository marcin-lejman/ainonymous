# Re-export from backend to keep eval.py working
from backend.analyzer import get_analyzer as build_analyzer, post_process, analyze_text  # noqa: F401
