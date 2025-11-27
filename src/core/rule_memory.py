"""Rule Memory module for storing fluent rules.

This module provides a key-value store for RTEC fluent rules where:
- Key: fluent name (e.g., 'trawlSpeed', 'gap')
- Value: FluentEntry containing description, rules, and metadata
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class FluentEntry(BaseModel):
    """
    Represents a fluent's rules and metadata.
    
    Attributes:
        name: The fluent identifier (e.g., 'gap', 'trawlSpeed').
        description: Natural language description of the fluent.
        rules: The validated RTEC rules as a string.
        score: Optional evaluation score (0.0 to 1.0) from validation.
        created_at: Timestamp when the entry was created.
        metadata: Extensible dictionary for additional data
                  (e.g., dependencies, domain, fluent_type).
    """
    
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    rules: str = Field(..., min_length=1)
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Fluent name cannot be empty")
        return v.strip()
    
    @field_validator("rules")
    @classmethod
    def rules_not_empty(cls, v: str) -> str:
        """Validate that rules are not empty or whitespace."""
        if not v.strip():
            raise ValueError("Rules cannot be empty")
        return v

    model_config = {
        "frozen": False,  # Allow updates
        "extra": "forbid",
    }


class RuleMemory:
    """
    Key-value store for fluent rules.
    
    Provides CRUD operations for FluentEntry objects, with
    specialized retrieval methods for prompt injection.
    
    The design supports future extension with dependency graphs
    through the metadata field and extensible query methods.
    
    Example:
        >>> memory = RuleMemory()
        >>> memory.add_entry(
        ...     name="gap",
        ...     description="Communication gap activity.",
        ...     rules="initiatedAt(gap(Vessel)=nearPort, T):- ..."
        ... )
        >>> memory.get_rules("gap")
        'initiatedAt(gap(Vessel)=nearPort, T):- ...'
    """
    
    def __init__(self):
        """Initialize an empty rule memory."""
        self._entries: Dict[str, FluentEntry] = {}
    
    def __len__(self) -> int:
        """Return the number of entries in memory."""
        return len(self._entries)
    
    def is_empty(self) -> bool:
        """Check if memory has no entries."""
        return len(self._entries) == 0
    
    def add(self, entry: FluentEntry) -> None:
        """
        Add a FluentEntry to memory.
        
        Args:
            entry: The FluentEntry to add.
            
        Note:
            If an entry with the same name exists, it will be overwritten.
        """
        self._entries[entry.name] = entry
    
    def add_entry(
        self,
        name: str,
        description: str,
        rules: str,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FluentEntry:
        """
        Add an entry using keyword arguments.
        
        Args:
            name: The fluent identifier.
            description: Natural language description.
            rules: The RTEC rules as a string.
            score: Optional evaluation score.
            metadata: Optional metadata dictionary.
            
        Returns:
            The created FluentEntry.
        """
        entry = FluentEntry(
            name=name,
            description=description,
            rules=rules,
            score=score,
            metadata=metadata or {}
        )
        self.add(entry)
        return entry
    
    def get(self, name: str) -> Optional[FluentEntry]:
        """
        Retrieve a FluentEntry by name.
        
        Args:
            name: The fluent identifier.
            
        Returns:
            The FluentEntry if found, None otherwise.
        """
        return self._entries.get(name)
    
    def contains(self, name: str) -> bool:
        """
        Check if a fluent exists in memory.
        
        Args:
            name: The fluent identifier.
            
        Returns:
            True if the fluent exists, False otherwise.
        """
        return name in self._entries
    
    def update(
        self,
        name: str,
        description: Optional[str] = None,
        rules: Optional[str] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FluentEntry:
        """
        Update an existing entry.
        
        Args:
            name: The fluent identifier.
            description: New description (if provided).
            rules: New rules (if provided).
            score: New score (if provided).
            metadata: New metadata (if provided, replaces existing).
            
        Returns:
            The updated FluentEntry.
            
        Raises:
            KeyError: If the fluent doesn't exist.
        """
        if name not in self._entries:
            raise KeyError(f"Fluent '{name}' not found in memory")
        
        entry = self._entries[name]
        
        # Create updated entry with new values
        updated_entry = FluentEntry(
            name=entry.name,
            description=description if description is not None else entry.description,
            rules=rules if rules is not None else entry.rules,
            score=score if score is not None else entry.score,
            created_at=entry.created_at,  # Preserve original timestamp
            metadata=metadata if metadata is not None else entry.metadata
        )
        
        self._entries[name] = updated_entry
        return updated_entry
    
    def remove(self, name: str) -> FluentEntry:
        """
        Remove an entry from memory.
        
        Args:
            name: The fluent identifier.
            
        Returns:
            The removed FluentEntry.
            
        Raises:
            KeyError: If the fluent doesn't exist.
        """
        if name not in self._entries:
            raise KeyError(f"Fluent '{name}' not found in memory")
        
        return self._entries.pop(name)
    
    def clear(self) -> None:
        """Remove all entries from memory."""
        self._entries.clear()
    
    def list_names(self) -> List[str]:
        """
        Get a list of all fluent names in memory.
        
        Returns:
            List of fluent names.
        """
        return list(self._entries.keys())
    
    def get_all(self) -> List[FluentEntry]:
        """
        Get all entries in memory.
        
        Returns:
            List of all FluentEntry objects.
        """
        return list(self._entries.values())
    
    def get_many(self, names: List[str]) -> List[FluentEntry]:
        """
        Get multiple entries by name.
        
        Args:
            names: List of fluent identifiers.
            
        Returns:
            List of FluentEntry objects (only those that exist).
        """
        return [
            self._entries[name]
            for name in names
            if name in self._entries
        ]
    
    # ==================== Specialized Retrieval ====================
    
    def get_rules(self, name: str) -> Optional[str]:
        """
        Get just the rules for a fluent.
        
        Args:
            name: The fluent identifier.
            
        Returns:
            The rules string if found, None otherwise.
        """
        entry = self.get(name)
        return entry.rules if entry else None
    
    def get_description(self, name: str) -> Optional[str]:
        """
        Get just the description for a fluent.
        
        Args:
            name: The fluent identifier.
            
        Returns:
            The description string if found, None otherwise.
        """
        entry = self.get(name)
        return entry.description if entry else None
    
    def get_formatted_rules(
        self,
        names: List[str],
        include_description: bool = False
    ) -> str:
        """
        Get formatted rules for multiple fluents.
        
        This is designed for injection into LLM prompts.
        
        Args:
            names: List of fluent identifiers.
            include_description: Whether to include descriptions.
            
        Returns:
            Formatted string with rules for each fluent.
        """
        parts = []
        
        for name in names:
            entry = self.get(name)
            if entry:
                section = [f"% === {name} ==="]
                if include_description and entry.description:
                    section.append(f"% Description: {entry.description}")
                section.append(entry.rules)
                parts.append("\n".join(section))
        
        return "\n\n".join(parts)
    
    # ==================== Filtering (Extensibility) ====================
    
    def filter_by_metadata(
        self,
        key: str,
        value: Any
    ) -> List[FluentEntry]:
        """
        Filter entries by metadata key-value pair.
        
        Args:
            key: The metadata key to filter on.
            value: The expected value.
            
        Returns:
            List of matching FluentEntry objects.
        """
        return [
            entry for entry in self._entries.values()
            if entry.metadata.get(key) == value
        ]
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Export memory to a dictionary.
        
        Returns:
            Dictionary representation of all entries.
        """
        return {
            name: {
                "description": entry.description,
                "rules": entry.rules,
                "score": entry.score,
                "created_at": entry.created_at.isoformat(),
                "metadata": entry.metadata
            }
            for name, entry in self._entries.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> "RuleMemory":
        """
        Create a RuleMemory from a dictionary.
        
        Args:
            data: Dictionary with fluent names as keys.
            
        Returns:
            New RuleMemory instance with loaded entries.
        """
        memory = cls()
        
        for name, entry_data in data.items():
            # Parse created_at if it's a string
            created_at = entry_data.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            entry = FluentEntry(
                name=name,
                description=entry_data.get("description", ""),
                rules=entry_data["rules"],
                score=entry_data.get("score"),
                created_at=created_at or datetime.now(),
                metadata=entry_data.get("metadata", {})
            )
            memory.add(entry)
        
        return memory

