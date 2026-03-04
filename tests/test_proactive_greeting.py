"""
Tests for build_intro_message() — hidden intro message for first-visit greeting.

Replaces old tests for generate_proactive_greeting (removed in greeting unification).
"""

import pytest

from api.learner_chat_service import build_intro_message


class TestBuildIntroMessage:
    """Test hidden intro message construction from learner profile."""

    def test_english_default(self):
        """English intro includes name, role, job, and familiarity."""
        profile = {
            "name": "Alice",
            "role": "Data Analyst",
            "job_description": "Analyzing sales data",
            "ai_familiarity": "beginner",
        }
        result = build_intro_message(profile, "en-US")
        assert "Alice" in result
        assert "Data Analyst" in result
        assert "Analyzing sales data" in result
        assert "beginner" in result
        assert "Let's start the lesson" in result

    def test_french(self):
        """French locale produces French intro."""
        profile = {
            "name": "Marie",
            "role": "Analyste",
            "job_description": "Analyse de données",
            "ai_familiarity": "intermediate",
        }
        result = build_intro_message(profile, "fr-FR")
        assert "Marie" in result
        assert "Analyste" in result
        assert "Analyse de données" in result
        assert "Commençons le cours" in result

    def test_portuguese(self):
        """Portuguese locale produces Portuguese intro."""
        profile = {
            "name": "João",
            "role": "Engenheiro",
            "ai_familiarity": "advanced",
        }
        result = build_intro_message(profile, "pt-BR")
        assert "João" in result
        assert "Engenheiro" in result
        assert "Vamos começar" in result

    def test_simplified_chinese(self):
        """Simplified Chinese locale."""
        profile = {"name": "李明", "role": "工程师", "ai_familiarity": "beginner"}
        result = build_intro_message(profile, "zh-CN")
        assert "李明" in result
        assert "工程师" in result

    def test_traditional_chinese(self):
        """Traditional Chinese locale."""
        profile = {"name": "陳小明", "role": "分析師", "ai_familiarity": "intermediate"}
        result = build_intro_message(profile, "zh-TW")
        assert "陳小明" in result
        assert "分析師" in result

    def test_missing_name_uses_fallback(self):
        """Missing name falls back to 'there'."""
        profile = {"role": "Student", "ai_familiarity": "beginner"}
        result = build_intro_message(profile, "en-US")
        assert "there" in result

    def test_missing_role_uses_fallback(self):
        """Missing role falls back to 'a learner'."""
        profile = {"name": "Bob", "ai_familiarity": "beginner"}
        result = build_intro_message(profile, "en-US")
        assert "a learner" in result

    def test_empty_job_description_omitted(self):
        """Empty job_description is not included in output."""
        profile = {
            "name": "Eve",
            "role": "Student",
            "job_description": "",
            "ai_familiarity": "beginner",
        }
        result = build_intro_message(profile, "en-US")
        # Should not have double spaces from empty job insertion
        assert "  " not in result

    def test_unknown_language_defaults_to_english(self):
        """Unknown language code falls back to English."""
        profile = {"name": "Test", "role": "Student", "ai_familiarity": "beginner"}
        result = build_intro_message(profile, "ja-JP")
        assert "Let's start the lesson" in result

    def test_empty_profile(self):
        """Completely empty profile uses all fallback values."""
        result = build_intro_message({}, "en-US")
        assert "there" in result
        assert "a learner" in result
        assert "intermediate" in result
