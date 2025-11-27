"""Tests for the Rule Memory module.

The RuleMemory provides a key-value store for fluent rules where:
- Key: fluent name (e.g., 'trawlSpeed', 'gap')
- Value: FluentEntry containing description and rules

Designed to be extensible for dependency graph integration.
"""

import pytest
from datetime import datetime

from src.core.rule_memory import FluentEntry, RuleMemory


class TestFluentEntry:
    """Tests for the FluentEntry data model."""

    def test_create_fluent_entry_with_required_fields(self):
        """FluentEntry can be created with name, description, and rules."""
        entry = FluentEntry(
            name="gap",
            description="A communication gap starts when we stop receiving messages.",
            rules="initiatedAt(gap(Vessel)=nearPort, T):- ..."
        )
        
        assert entry.name == "gap"
        assert "communication gap" in entry.description
        assert "initiatedAt" in entry.rules

    def test_fluent_entry_has_optional_score(self):
        """FluentEntry can store the evaluation score."""
        entry = FluentEntry(
            name="lowSpeed",
            description="The vessel is moving at low speed.",
            rules="initiatedAt(lowSpeed(Vessel)=true, T):- ...",
            score=0.95
        )
        
        assert entry.score == 0.95

    def test_fluent_entry_has_optional_metadata(self):
        """FluentEntry can store arbitrary metadata for extensibility."""
        entry = FluentEntry(
            name="trawling",
            description="Trawling is a fishing method.",
            rules="holdsFor(trawling(Vessel)=true, I):- ...",
            metadata={
                "domain": "MSA",
                "fluent_type": "composite",
                "dependencies": ["trawlSpeed", "trawlingMovement"]
            }
        )
        
        assert entry.metadata["domain"] == "MSA"
        assert entry.metadata["fluent_type"] == "composite"
        assert "trawlSpeed" in entry.metadata["dependencies"]

    def test_fluent_entry_has_created_at_timestamp(self):
        """FluentEntry tracks when it was created."""
        before = datetime.now()
        entry = FluentEntry(
            name="gap",
            description="Communication gap.",
            rules="..."
        )
        after = datetime.now()
        
        assert entry.created_at is not None
        assert before <= entry.created_at <= after

    def test_fluent_entry_name_cannot_be_empty(self):
        """FluentEntry name must not be empty."""
        with pytest.raises(ValueError):
            FluentEntry(
                name="",
                description="Some description",
                rules="some rules"
            )

    def test_fluent_entry_rules_cannot_be_empty(self):
        """FluentEntry rules must not be empty."""
        with pytest.raises(ValueError):
            FluentEntry(
                name="gap",
                description="Some description",
                rules=""
            )

    def test_fluent_entry_description_can_be_empty(self):
        """FluentEntry description can be empty (for imported rules)."""
        entry = FluentEntry(
            name="gap",
            description="",
            rules="initiatedAt(gap(Vessel)=nearPort, T):- ..."
        )
        
        assert entry.description == ""


class TestRuleMemory:
    """Tests for the RuleMemory store."""

    def test_create_empty_memory(self):
        """RuleMemory can be created empty."""
        memory = RuleMemory()
        
        assert len(memory) == 0
        assert memory.is_empty()

    def test_add_and_retrieve_entry(self):
        """Can add a FluentEntry and retrieve it by name."""
        memory = RuleMemory()
        
        entry = FluentEntry(
            name="gap",
            description="Communication gap description.",
            rules="initiatedAt(gap(Vessel)=nearPort, T):- ..."
        )
        
        memory.add(entry)
        
        retrieved = memory.get("gap")
        assert retrieved is not None
        assert retrieved.name == "gap"
        assert retrieved.rules == entry.rules

    def test_add_entry_directly_with_kwargs(self):
        """Can add an entry using keyword arguments."""
        memory = RuleMemory()
        
        memory.add_entry(
            name="lowSpeed",
            description="Low speed activity.",
            rules="initiatedAt(lowSpeed(Vessel)=true, T):- ..."
        )
        
        assert memory.contains("lowSpeed")
        entry = memory.get("lowSpeed")
        assert "Low speed" in entry.description

    def test_get_nonexistent_entry_returns_none(self):
        """Getting a non-existent entry returns None."""
        memory = RuleMemory()
        
        result = memory.get("nonexistent")
        
        assert result is None

    def test_contains_checks_existence(self):
        """Contains method checks if fluent exists in memory."""
        memory = RuleMemory()
        memory.add_entry(
            name="gap",
            description="Gap description.",
            rules="..."
        )
        
        assert memory.contains("gap") is True
        assert memory.contains("other") is False

    def test_update_existing_entry(self):
        """Can update an existing entry with new rules."""
        memory = RuleMemory()
        
        memory.add_entry(
            name="gap",
            description="Original description.",
            rules="original_rules"
        )
        
        memory.update(
            name="gap",
            rules="updated_rules",
            score=0.98
        )
        
        entry = memory.get("gap")
        assert entry.rules == "updated_rules"
        assert entry.score == 0.98
        assert entry.description == "Original description."  # Unchanged

    def test_update_nonexistent_raises_error(self):
        """Updating a non-existent entry raises KeyError."""
        memory = RuleMemory()
        
        with pytest.raises(KeyError):
            memory.update(name="nonexistent", rules="new_rules")

    def test_remove_entry(self):
        """Can remove an entry from memory."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="...", rules="...")
        
        memory.remove("gap")
        
        assert memory.contains("gap") is False

    def test_remove_nonexistent_raises_error(self):
        """Removing a non-existent entry raises KeyError."""
        memory = RuleMemory()
        
        with pytest.raises(KeyError):
            memory.remove("nonexistent")

    def test_len_returns_entry_count(self):
        """len() returns the number of entries."""
        memory = RuleMemory()
        
        assert len(memory) == 0
        
        memory.add_entry(name="gap", description="...", rules="...")
        memory.add_entry(name="lowSpeed", description="...", rules="...")
        
        assert len(memory) == 2

    def test_list_all_fluent_names(self):
        """Can list all fluent names in memory."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="...", rules="...")
        memory.add_entry(name="lowSpeed", description="...", rules="...")
        memory.add_entry(name="trawling", description="...", rules="...")
        
        names = memory.list_names()
        
        assert set(names) == {"gap", "lowSpeed", "trawling"}

    def test_get_all_entries(self):
        """Can retrieve all entries."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="Gap desc", rules="gap rules")
        memory.add_entry(name="lowSpeed", description="Low desc", rules="low rules")
        
        entries = memory.get_all()
        
        assert len(entries) == 2
        assert all(isinstance(e, FluentEntry) for e in entries)


class TestRuleMemoryRetrieval:
    """Tests for specialized retrieval methods."""

    def test_get_rules_only(self):
        """Can retrieve just the rules for a fluent."""
        memory = RuleMemory()
        memory.add_entry(
            name="gap",
            description="Communication gap.",
            rules="initiatedAt(gap(Vessel)=nearPort, T):- ..."
        )
        
        rules = memory.get_rules("gap")
        
        assert rules == "initiatedAt(gap(Vessel)=nearPort, T):- ..."

    def test_get_rules_for_nonexistent_returns_none(self):
        """Getting rules for non-existent fluent returns None."""
        memory = RuleMemory()
        
        assert memory.get_rules("nonexistent") is None

    def test_get_description_only(self):
        """Can retrieve just the description for a fluent."""
        memory = RuleMemory()
        memory.add_entry(
            name="gap",
            description="Communication gap description.",
            rules="..."
        )
        
        desc = memory.get_description("gap")
        
        assert desc == "Communication gap description."

    def test_get_formatted_rules_for_multiple(self):
        """Can get formatted rules for multiple fluents (for prompt injection)."""
        memory = RuleMemory()
        memory.add_entry(
            name="trawlSpeed",
            description="Trawl speed activity.",
            rules="initiatedAt(trawlSpeed(V)=true, T):- speed_check."
        )
        memory.add_entry(
            name="trawlingMovement",
            description="Trawling movement activity.",
            rules="initiatedAt(trawlingMovement(V)=true, T):- heading_change."
        )
        
        formatted = memory.get_formatted_rules(["trawlSpeed", "trawlingMovement"])
        
        assert "% === trawlSpeed ===" in formatted
        assert "% === trawlingMovement ===" in formatted
        assert "speed_check" in formatted
        assert "heading_change" in formatted

    def test_get_formatted_rules_skips_missing(self):
        """Formatted rules silently skips fluents not in memory."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="...", rules="gap_rules")
        
        formatted = memory.get_formatted_rules(["gap", "nonexistent"])
        
        assert "gap_rules" in formatted
        assert "nonexistent" not in formatted


class TestRuleMemorySerialization:
    """Tests for serialization/persistence (extensibility)."""

    def test_export_to_dict(self):
        """Can export memory to a dictionary."""
        memory = RuleMemory()
        memory.add_entry(
            name="gap",
            description="Gap description.",
            rules="gap_rules",
            score=0.95
        )
        
        exported = memory.to_dict()
        
        assert "gap" in exported
        assert exported["gap"]["description"] == "Gap description."
        assert exported["gap"]["rules"] == "gap_rules"
        assert exported["gap"]["score"] == 0.95

    def test_import_from_dict(self):
        """Can create memory from a dictionary."""
        data = {
            "gap": {
                "description": "Gap description.",
                "rules": "gap_rules",
                "score": 0.95
            },
            "lowSpeed": {
                "description": "Low speed.",
                "rules": "low_rules"
            }
        }
        
        memory = RuleMemory.from_dict(data)
        
        assert len(memory) == 2
        assert memory.get("gap").score == 0.95
        assert memory.get("lowSpeed").rules == "low_rules"

    def test_clear_removes_all_entries(self):
        """Clear removes all entries from memory."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="...", rules="...")
        memory.add_entry(name="lowSpeed", description="...", rules="...")
        
        memory.clear()
        
        assert len(memory) == 0
        assert memory.is_empty()


class TestRuleMemoryExtensibility:
    """Tests ensuring the design supports future dependency graph integration."""

    def test_metadata_preserved_on_retrieval(self):
        """Metadata is preserved when entry is retrieved."""
        memory = RuleMemory()
        memory.add_entry(
            name="trawling",
            description="Trawling activity.",
            rules="holdsFor(trawling(V)=true, I):- ...",
            metadata={
                "dependencies": ["trawlSpeed", "trawlingMovement"],
                "domain": "MSA"
            }
        )
        
        entry = memory.get("trawling")
        
        assert entry.metadata["dependencies"] == ["trawlSpeed", "trawlingMovement"]
        assert entry.metadata["domain"] == "MSA"

    def test_can_filter_by_domain_using_metadata(self):
        """Can filter entries by domain using metadata."""
        memory = RuleMemory()
        memory.add_entry(
            name="gap", description="...", rules="...",
            metadata={"domain": "MSA"}
        )
        memory.add_entry(
            name="lowSpeed", description="...", rules="...",
            metadata={"domain": "MSA"}
        )
        memory.add_entry(
            name="moving", description="...", rules="...",
            metadata={"domain": "HAR"}
        )
        
        msa_entries = memory.filter_by_metadata("domain", "MSA")
        
        assert len(msa_entries) == 2
        assert all(e.metadata["domain"] == "MSA" for e in msa_entries)

    def test_get_entries_by_names(self):
        """Can get multiple entries by a list of names."""
        memory = RuleMemory()
        memory.add_entry(name="gap", description="...", rules="gap_rules")
        memory.add_entry(name="lowSpeed", description="...", rules="low_rules")
        memory.add_entry(name="trawling", description="...", rules="trawl_rules")
        
        entries = memory.get_many(["gap", "trawling"])
        
        assert len(entries) == 2
        names = [e.name for e in entries]
        assert "gap" in names
        assert "trawling" in names
        assert "lowSpeed" not in names

