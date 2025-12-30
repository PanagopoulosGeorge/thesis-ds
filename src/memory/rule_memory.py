"""Rule Memory Module for storing and retrieving validated fluent definitions.

This module implements the RuleMemory component from the architecture diagram.
It provides external memory for stateless LLMs, storing previously learned
fluent definitions that can be retrieved and injected into future prompts.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger(__name__)


class RuleMemoryEntry:
    """Entry in the rule memory store.
    
    Stores a fluent's rules along with its evaluation score and metadata.
    """
    
    def __init__(
        self,
        fluent_name: str,
        rules: str,
        score: float,
        natural_language_description: Optional[str] = None,
        created_at: Optional[datetime] = None
        
    ):
        """Initialize a memory entry.
        
        Args:
            fluent_name: Name of the fluent
            rules: List of RTEC rules for this fluent
            score: Evaluation score (0.0 to 1.0)
            created_at: Timestamp when entry was created
        """
        if not fluent_name or not fluent_name.strip():
            raise ValueError("fluent_name cannot be empty")
        
        if not isinstance(rules, str):
            raise TypeError(f"rules must be a string, got {type(rules)}")
        
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"score must be between 0.0 and 1.0, got {score}")
        
        self.fluent_name = fluent_name.strip()
        self.rules = rules
        self.score = score
        self.created_at = created_at or datetime.utcnow()
        self.id = uuid4()
        self.natural_language_description = natural_language_description
    
    def __repr__(self) -> str:
        return (
            f"RuleMemoryEntry(fluent={self.fluent_name}, "
            f"rules={self.rules}, score={self.score:.3f}, "
            f"natural_language_description={self.natural_language_description})"
        )


class RuleMemory:
    """External memory system for storing and retrieving learned fluents.
    
    This class implements the RuleMemory component from the architecture diagram.
    It provides a persistent key-value store for RTEC fluent rules, enabling
    hierarchical prompting by storing prerequisite fluent definitions.
    
    Example:
        >>> memory = RuleMemory()
        >>> memory.add_entry("gap", rules, score=0.95)
        >>> prerequisites = memory.get_formatted_rules(["gap", "lowSpeed"])
        >>> # Use prerequisites in prompt...
    """
    
    def __init__(self, min_score_threshold: float = 0.0):
        """Initialize rule memory.
        
        Args:
            min_score_threshold: Minimum score required to store an entry.
                Entries with scores below this threshold will not be stored.
        """
        if not (0.0 <= min_score_threshold <= 1.0):
            raise ValueError(
                f"min_score_threshold must be between 0.0 and 1.0, "
                f"got {min_score_threshold}"
            )
        
        self._storage: Dict[str, RuleMemoryEntry] = {}
        self.min_score_threshold = min_score_threshold
        
        logger.info(
            "RuleMemory initialized",
            min_score_threshold=min_score_threshold,
        )
    
    def add_entry(
        self,
        fluent_name: str,
        rules: str,
        score: float,
        natural_language_description: Optional[str] = None,
    ) -> bool:
        """Add or update an entry in memory.
        
        Args:
            fluent_name: Name of the fluent
            rules: List of RTEC rules for this fluent
            score: Evaluation score (0.0 to 1.0)
            natural_language_description: Natural language description of the fluent
        Returns:
            True if entry was added/updated, False if score was too low
            
        Raises:
            ValueError: If fluent_name is empty or score is invalid
            TypeError: If rules is not a list
        """
        if score < self.min_score_threshold:
            logger.debug(
                "Entry rejected due to low score",
                fluent_name=fluent_name,
                score=score,
                threshold=self.min_score_threshold,
            )
            return False
        
        entry = RuleMemoryEntry(fluent_name, rules, score, natural_language_description)
        
        # Check if we're updating an existing entry
        is_update = fluent_name in self._storage
        old_score = self._storage[fluent_name].score if is_update else None
        
        self._storage[fluent_name] = entry
        
        logger.info(
            "Entry added to memory" if not is_update else "Entry updated in memory",
            fluent_name=fluent_name,
            rules_count=len(rules),
            score=score,
            old_score=old_score,
            natural_language_description=natural_language_description,
        )
        
        return True
    
    def get_entry(self, fluent_name: str) -> Optional[RuleMemoryEntry]:
        """Get an entry by fluent name.
        
        Args:
            fluent_name: Name of the fluent to retrieve
            
        Returns:
            RuleMemoryEntry if found, None otherwise
        """
        return self._storage.get(fluent_name)
    
    def get_rules(self, fluent_name: str) -> Optional[str]:
        """Get rules for a fluent.
        
        Args:
            fluent_name: Name of the fluent
            
        Returns:
            List of RTEC rules if found, None otherwise
        """
        entry = self.get_entry(fluent_name)
        return entry.rules if entry else None
    
    def has_entry(self, fluent_name: str) -> bool:
        """Check if an entry exists.
        
        Args:
            fluent_name: Name of the fluent
            
        Returns:
            True if entry exists, False otherwise
        """
        return fluent_name in self._storage
    
    def get_formatted_rules(
        self,
        fluent_names: List[str],
        format_style: str = "prolog",
    ) -> str:
        """Get formatted rules for multiple fluents.
        
        This method formats prerequisite rules for injection into prompts.
        It's used by the PromptBuilder to include context when generating
        composite fluents.
        
        Args:
            fluent_names: List of fluent names to retrieve
            format_style: Format style ("prolog" or "markdown")
            
        Returns:
            Formatted string containing all rules
            
        Raises:
            ValueError: If any fluent name is not found in memory
        """
        if not fluent_names:
            return ""
        
        missing_fluents = [
            name for name in fluent_names if not self.has_entry(name)
        ]
        
        if missing_fluents:
            raise ValueError(
                f"Missing fluents in memory: {', '.join(missing_fluents)}. "
                f"Available fluents: {', '.join(self._storage.keys())}"
            )
        
        entries = [self._storage[name] for name in fluent_names]
        
        if format_style == "prolog":
            return self._format_as_prolog(entries)
        elif format_style == "markdown":
            return self._format_as_markdown(entries)
        else:
            raise ValueError(f"Unknown format_style: {format_style}")
    
    def _format_as_prolog(self, entries: List[RuleMemoryEntry]) -> str:
        """Format entries as Prolog/RTEC syntax.
        
        Args:
            entries: List of memory entries to format
            
        Returns:
            Formatted Prolog string
        """
        lines = []
        lines.append("% Prerequisite fluent definitions:")
        lines.append("")
        
        for entry in entries:
            lines.append(f"% Fluent: {entry.fluent_name} (score: {entry.score:.3f})")
            for rule in entry.rules:
                lines.append(rule)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_as_markdown(self, entries: List[RuleMemoryEntry]) -> str:
        """Format entries as Markdown.
        
        Args:
            entries: List of memory entries to format
            
        Returns:
            Formatted Markdown string
        """
        lines = []
        lines.append("## Prerequisite Fluent Definitions\n")
        
        for entry in entries:
            lines.append(f"### {entry.fluent_name} (score: {entry.score:.3f})\n")
            lines.append("```prolog")
            for rule in entry.rules:
                lines.append(rule)
            lines.append("```\n")
        
        return "\n".join(lines)
    
    def list_fluents(self) -> List[str]:
        """List all fluent names in memory.
        
        Returns:
            List of fluent names
        """
        return list(self._storage.keys())
    
    def get_statistics(self) -> Dict[str, any]:
        """Get memory statistics.
        
        Returns:
            Dictionary with statistics about the memory
        """
        if not self._storage:
            return {
                "total_entries": 0,
                "average_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
            }
        
        scores = [entry.score for entry in self._storage.values()]
        
        return {
            "total_entries": len(self._storage),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "fluent_names": list(self._storage.keys()),
        }
    
    def clear(self) -> None:
        """Clear all entries from memory."""
        count = len(self._storage)
        self._storage.clear()
        logger.info("Memory cleared", entries_removed=count)
    
    def remove_entry(self, fluent_name: str) -> bool:
        """Remove an entry from memory.
        
        Args:
            fluent_name: Name of the fluent to remove
            
        Returns:
            True if entry was removed, False if it didn't exist
        """
        if fluent_name in self._storage:
            del self._storage[fluent_name]
            logger.info("Entry removed from memory", fluent_name=fluent_name)
            return True
        return False

