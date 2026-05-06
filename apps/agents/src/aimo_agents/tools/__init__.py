"""Tool registry exposed as one import surface."""

from .create_quiz import create_quiz
from .generate_report import class_overview, quiz_stats, student_report
from .record_score import record_score
from .retrieve_material import retrieve_material
from .send_analytics import send_analytics

tools = [retrieve_material, create_quiz, record_score, send_analytics, student_report, class_overview, quiz_stats]
tools_by_name = {tool.name: tool for tool in tools}

__all__ = [
    "class_overview",
    "create_quiz",
    "quiz_stats",
    "record_score",
    "retrieve_material",
    "send_analytics",
    "student_report",
    "tools",
    "tools_by_name",
]