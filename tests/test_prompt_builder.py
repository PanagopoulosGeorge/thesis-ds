"""Tests for prompt builder functionality."""

import pytest

from src.prompts.builder import (
    BasePromptBuilder,
    HARPromptBuilder,
    MSAPromptBuilder,
)


class TestMSAPromptBuilder:
    """Tests for MSAPromptBuilder."""

    def setup_method(self):
        """Setup test fixtures."""
        self.builder = MSAPromptBuilder()

    def test_build_initial_gap(self):
        """Test build_initial for 'gap' activity."""
        messages = self.builder.build_initial("gap")

        # Verify structure
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Verify system message contains all required components
        system_content = messages[0]["content"]

        # Check RTEC base prompts
        assert "Run-Time Event Calculus" in system_content
        assert "RTEC" in system_content
        assert "happensAt" in system_content
        assert "holdsAt" in system_content
        assert "initiatedAt" in system_content
        assert "terminatedAt" in system_content

        # Check fluent definitions
        assert "simple fluent" in system_content
        assert "statically determined fluent" in system_content

        # Check MSA domain info
        assert "maritime situational awareness" in system_content.lower()
        assert "MSA" in system_content
        assert "Vessel" in system_content

        # Check MSA events are present
        assert "change_in_speed_start" in system_content
        assert "gap_start" in system_content
        assert "entersArea" in system_content

        # Check MSA background knowledge
        assert "thresholds" in system_content

        # Check examples are present
        assert "Example" in system_content
        assert "withinArea" in system_content or "stopped" in system_content

        # Verify user message contains activity description
        user_content = messages[1]["content"]
        assert '"gap"' in user_content.lower() or "gap" in user_content
        assert "communication gap" in user_content.lower()

    def test_build_initial_highSpeedNearCoast(self):
        """Test build_initial for 'highSpeedNearCoast' activity."""
        messages = self.builder.build_initial("highSpeedNearCoast")

        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "highspeednearcoast" in user_content.lower()
        assert "coastal" in user_content.lower() or "coast" in user_content.lower()

    def test_build_initial_invalid_activity(self):
        """Test build_initial with invalid activity name."""
        with pytest.raises(ValueError) as exc_info:
            self.builder.build_initial("invalid_activity_name")

        assert "not found" in str(exc_info.value).lower()
        assert "invalid_activity_name" in str(exc_info.value)

    def test_build_refinement(self):
        """Test build_refinement with feedback."""
        prev_rules = """
        initiatedAt(gap(Vessel)=nearPorts, T) :-
            happensAt(gap_start(Vessel), T),
            holdsAt(withinArea(Vessel, nearPorts)=true, T).
        """

        feedback = """
        The rule is missing the farFromPorts case.
        Please add a second initiatedAt rule for when the gap starts far from ports.
        """

        messages = self.builder.build_refinement(
            activity="gap",
            prev_rules=prev_rules,
            feedback=feedback,
            attempt=2
        )

        # Verify structure
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Verify system message is complete (same as initial)
        system_content = messages[0]["content"]
        assert "RTEC" in system_content
        assert "maritime situational awareness" in system_content.lower()

        # Verify user message contains refinement context
        user_content = messages[1]["content"]
        assert "attempt 2" in user_content.lower()
        assert "gap" in user_content.lower()
        assert prev_rules.strip() in user_content
        assert feedback.strip() in user_content
        assert "previous" in user_content.lower()
        assert "feedback" in user_content.lower()

    def test_activity_map_populated(self):
        """Test that activity map is correctly populated."""
        # Check that common MSA activities are available
        expected_activities = [
            "gap",
            "highSpeedNearCoast",
            "trawlSpeed",
            "lowSpeed",
            "trawling",
            "loitering",
        ]

        for activity in expected_activities:
            assert activity in self.builder.activity_map


class TestHARPromptBuilder:
    """Tests for HARPromptBuilder."""

    def setup_method(self):
        """Setup test fixtures."""
        self.builder = HARPromptBuilder()

    def test_build_initial_leaving_object(self):
        """Test build_initial for 'leaving_object' activity."""
        messages = self.builder.build_initial("leaving_object")

        # Verify structure
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Verify system message contains HAR-specific content
        system_content = messages[0]["content"]

        # Check RTEC base is there
        assert "RTEC" in system_content

        # Check HAR domain info
        assert "human activity recognition" in system_content.lower()
        assert "HAR" in system_content

        # Check HAR events
        assert "appear" in system_content
        assert "disappear" in system_content

        # Check HAR fluents
        assert "walking" in system_content
        assert "coord" in system_content or "close" in system_content

        # Verify user message
        user_content = messages[1]["content"]
        assert "leaving_object" in user_content

    def test_build_initial_moving(self):
        """Test build_initial for 'moving' activity."""
        messages = self.builder.build_initial("moving")

        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "moving" in user_content.lower()
        assert "walking" in user_content.lower()

    def test_build_initial_fighting(self):
        """Test build_initial for 'fighting' activity."""
        messages = self.builder.build_initial("fighting")

        assert len(messages) == 2
        user_content = messages[1]["content"]
        assert "fighting" in user_content.lower()
        assert "abrupt" in user_content.lower()

    def test_build_refinement(self):
        """Test build_refinement for HAR activity."""
        prev_rules = """
        initiatedAt(leaving_object(Person, Object)=true, T) :-
            happensAt(appear(Object), T).
        """

        feedback = """
        Missing condition: the person must be close to the object when it appears.
        Add holdsAt(close(Person, Object, 10)=true, T) to the body.
        """

        messages = self.builder.build_refinement(
            activity="leaving_object",
            prev_rules=prev_rules,
            feedback=feedback,
            attempt=2
        )

        user_content = messages[1]["content"]
        assert "attempt 2" in user_content.lower()
        assert prev_rules.strip() in user_content
        assert feedback.strip() in user_content

    def test_activity_map_populated(self):
        """Test that activity map is correctly populated."""
        expected_activities = ["leaving_object", "moving", "fighting"]

        for activity in expected_activities:
            assert activity in self.builder.activity_map


class TestBasePromptBuilder:
    """Tests for BasePromptBuilder abstract class."""

    def test_cannot_instantiate(self):
        """Test that BasePromptBuilder cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePromptBuilder()


class TestPromptBuilderIntegration:
    """Integration tests for prompt builders."""

    def test_msa_and_har_have_different_content(self):
        """Test that MSA and HAR builders produce different content."""
        msa_builder = MSAPromptBuilder()
        har_builder = HARPromptBuilder()

        msa_messages = msa_builder.build_initial("gap")
        har_messages = har_builder.build_initial("leaving_object")

        # System messages should be different
        msa_system = msa_messages[0]["content"]
        har_system = har_messages[0]["content"]

        # Check domain-specific content
        assert "maritime" in msa_system.lower()
        assert "human activity" in har_system.lower()

        assert "Vessel" in msa_system
        assert "Person" in har_system

    def test_refinement_includes_attempt_number(self):
        """Test that attempt number appears in refinement prompts."""
        builder = MSAPromptBuilder()

        for attempt in [2, 3, 4, 5]:
            messages = builder.build_refinement(
                activity="gap",
                prev_rules="some rules",
                feedback="some feedback",
                attempt=attempt
            )

            user_content = messages[1]["content"]
            assert f"attempt {attempt}" in user_content.lower()
            assert f"attempt {attempt - 1}" in user_content.lower()

    def test_system_message_consistency(self):
        """Test that system message is consistent between initial and refinement."""
        builder = MSAPromptBuilder()

        initial_messages = builder.build_initial("gap")
        refinement_messages = builder.build_refinement(
            activity="gap",
            prev_rules="rules",
            feedback="feedback",
            attempt=2
        )

        # System messages should be identical
        assert initial_messages[0]["content"] == refinement_messages[0]["content"]


class TestFluentTypeParameter:
    """Tests for fluent_type parameter in prompt building."""

    def setup_method(self):
        """Setup test fixtures."""
        self.msa_builder = MSAPromptBuilder()
        self.har_builder = HARPromptBuilder()

    def test_build_initial_with_simple_fluent_type(self):
        """Test build_initial with fluent_type='simple'."""
        messages = self.msa_builder.build_initial("gap", fluent_type="simple")

        system_content = messages[0]["content"]

        # Should include examples section
        assert "=== Examples ===" in system_content

        # Verify it contains simple fluent examples
        # (withinArea and stopped are simple fluent examples)
        assert "withinArea" in system_content or "initiatedAt" in system_content

    def test_build_initial_with_static_fluent_type(self):
        """Test build_initial with fluent_type='static'."""
        messages = self.msa_builder.build_initial("gap", fluent_type="static")

        system_content = messages[0]["content"]

        # Should include examples section
        assert "=== Examples ===" in system_content

        # Verify it contains static fluent examples
        # (underWay and rendezVous are static fluent examples)
        assert "underWay" in system_content or "holdsFor" in system_content

    def test_build_initial_with_both_fluent_type(self):
        """Test build_initial with fluent_type='both' (default)."""
        messages_both = self.msa_builder.build_initial("gap", fluent_type="both")
        messages_default = self.msa_builder.build_initial("gap")

        # Both should be identical
        assert messages_both[0]["content"] == messages_default[0]["content"]

    def test_build_refinement_with_fluent_type(self):
        """Test build_refinement with fluent_type parameter."""
        messages_simple = self.msa_builder.build_refinement(
            activity="gap",
            prev_rules="rules",
            feedback="feedback",
            attempt=2,
            fluent_type="simple"
        )

        messages_static = self.msa_builder.build_refinement(
            activity="gap",
            prev_rules="rules",
            feedback="feedback",
            attempt=2,
            fluent_type="static"
        )

        # System messages should differ based on fluent_type
        assert messages_simple[0]["content"] != messages_static[0]["content"]

        # User messages should be identical (same refinement context)
        assert messages_simple[1]["content"] == messages_static[1]["content"]

    def test_fluent_type_affects_message_length(self):
        """Test that fluent_type parameter affects system message length."""
        messages_simple = self.msa_builder.build_initial("gap", fluent_type="simple")
        messages_static = self.msa_builder.build_initial("gap", fluent_type="static")
        messages_both = self.msa_builder.build_initial("gap", fluent_type="both")

        len_simple = len(messages_simple[0]["content"])
        len_static = len(messages_static[0]["content"])
        len_both = len(messages_both[0]["content"])

        # 'both' should be longer than either 'simple' or 'static'
        assert len_both > len_simple
        assert len_both > len_static

    def test_har_builder_supports_fluent_type(self):
        """Test that HAR builder also supports fluent_type parameter."""
        messages_simple = self.har_builder.build_initial(
            "leaving_object",
            fluent_type="simple"
        )
        messages_static = self.har_builder.build_initial(
            "leaving_object",
            fluent_type="static"
        )

        # Should generate different messages
        assert messages_simple[0]["content"] != messages_static[0]["content"]

        # Both should have valid structure
        assert len(messages_simple) == 2
        assert len(messages_static) == 2
        assert messages_simple[0]["role"] == "system"
        assert messages_static[0]["role"] == "system"
