"""Data models for Genova Weekly Informal Outings.

Defines the core data representations for activities, categories, and catalogs
adhering to interface contracts in PROJECT.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OutingCategory(str, Enum):
    """Normalized categories for informal leisure and cultural outings."""
    CINEMA = "cinema"
    MOSTRA = "mostra"
    PASSEGGIATA = "passeggiata"
    BIBLIOTECA = "biblioteca"
    LABORATORIO = "laboratorio"
    MUSICA = "musica"
    RITROVO = "ritrovo"
    ALTRO = "altro"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> OutingCategory:
        """Parse string to OutingCategory with safe fallback to ALTRO."""
        if not val:
            return cls.ALTRO
        if isinstance(val, OutingCategory):
            return val
        normalized = str(val).strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        # Common synonyms mapping
        synonyms = {
            "film": cls.CINEMA,
            "cinema_essai": cls.CINEMA,
            "cinema d'essai": cls.CINEMA,
            "cinema dessai": cls.CINEMA,
            "cinema-dessai": cls.CINEMA,
            "cineclub": cls.CINEMA,
            "cinema": cls.CINEMA,
            "mostre": cls.MOSTRA,
            "mostra": cls.MOSTRA,
            "museo": cls.MOSTRA,
            "musei": cls.MOSTRA,
            "arte": cls.MOSTRA,
            "walk": cls.PASSEGGIATA,
            "passeggiata": cls.PASSEGGIATA,
            "passeggiate": cls.PASSEGGIATA,
            "panorami": cls.PASSEGGIATA,
            "panorama": cls.PASSEGGIATA,
            "parco": cls.PASSEGGIATA,
            "parchi": cls.PASSEGGIATA,
            "belvedere": cls.PASSEGGIATA,
            "libri": cls.BIBLIOTECA,
            "libro": cls.BIBLIOTECA,
            "biblioteca": cls.BIBLIOTECA,
            "biblioteche": cls.BIBLIOTECA,
            "studio": cls.BIBLIOTECA,
            "workshop": cls.LABORATORIO,
            "laboratorio": cls.LABORATORIO,
            "laboratori": cls.LABORATORIO,
            "bottega": cls.LABORATORIO,
            "botteghe": cls.LABORATORIO,
            "artigianato": cls.LABORATORIO,
            "concerto": cls.MUSICA,
            "concerti": cls.MUSICA,
            "musica": cls.MUSICA,
            "live": cls.MUSICA,
            "teatro": cls.MUSICA,
            "bar": cls.RITROVO,
            "caffe": cls.RITROVO,
            "caffè": cls.RITROVO,
            "ritrovo": cls.RITROVO,
            "ritrovi": cls.RITROVO,
            "degustazione": cls.RITROVO,
            "aperitivo": cls.RITROVO,
            "sciamadda": cls.RITROVO,
            "sciamadde": cls.RITROVO,
            "altro": cls.ALTRO,
        }
        if normalized in synonyms:
            return synonyms[normalized]
        clean_norm = normalized.replace("'", " ").replace("-", " ").replace("_", " ").strip()
        if clean_norm in synonyms:
            return synonyms[clean_norm]
        return cls.ALTRO


@dataclass
class OutingOption:
    """Represents a single verified informal outing option in Genova or provincia.

    Attributes:
        id: Unique identifier slug (e.g. 'sivori_film_mer')
        title: Clean, descriptive title without em/en dashes
        category: OutingCategory enum
        venue: Name of the venue or place
        zone: City quarter or municipality (e.g. 'Centro', 'Nervi', 'Porto Antico')
        day_time: Opening days or scheduled times for the current week
        verified_url: Official, reachable HTTP/HTTPS source URL
        description: Direct, informal description in plain writing style
        source_type: 'verified_local' or 'live_web'
        is_weather_dependent: True for outdoor strolls/belvederes subject to rain/alert
        address: Full street address if applicable
        time_slot: Broad time slot ('mattina', 'pomeriggio', 'sera', 'flessibile')
        cost_info: Optional admission pricing details (e.g. 'Gratuito', 'Biglietto 7€')
        is_free: True if admission is free
        tags: Optional thematic keywords (e.g. ['indoor', 'panoramico'])
        raw_metadata: Original dataset attributes for reference
    """
    id: str
    title: str
    category: OutingCategory
    venue: str
    zone: str
    day_time: str
    verified_url: str
    description: str
    source_type: str = "verified_local"
    is_weather_dependent: bool = False
    address: str = ""
    time_slot: str = "flessibile"
    cost_info: Optional[str] = None
    is_free: bool = False
    tags: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source_url(self) -> str:
        """Compatibility alias for verified_url."""
        return self.verified_url

    @source_url.setter
    def source_url(self, value: str) -> None:
        self.verified_url = value

    @property
    def days_display(self) -> str:
        """Compatibility alias for day_time."""
        return self.day_time

    @days_display.setter
    def days_display(self, value: str) -> None:
        self.day_time = value

    @property
    def verified(self) -> bool:
        """Compatibility verification boolean."""
        return bool(self.verified_url)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OutingOption to serializable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value if isinstance(self.category, OutingCategory) else str(self.category),
            "venue": self.venue,
            "zone": self.zone,
            "day_time": self.day_time,
            "verified_url": self.verified_url,
            "description": self.description,
            "source_type": self.source_type,
            "is_weather_dependent": self.is_weather_dependent,
            "address": self.address,
            "time_slot": self.time_slot,
            "cost_info": self.cost_info,
            "is_free": self.is_free,
            "tags": list(self.tags),
            "raw_metadata": dict(self.raw_metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutingOption:
        """Construct OutingOption from dictionary with graceful defaults."""
        cat_raw = data.get("category", OutingCategory.ALTRO)
        if isinstance(cat_raw, OutingCategory):
            cat = cat_raw
        else:
            cat = OutingCategory.from_str(str(cat_raw))

        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            category=cat,
            venue=str(data.get("venue", "")),
            zone=str(data.get("zone", "")),
            day_time=str(data.get("day_time", data.get("days_display", ""))),
            verified_url=str(data.get("verified_url", data.get("source_url", ""))),
            description=str(data.get("description", "")),
            source_type=str(data.get("source_type", "verified_local")),
            is_weather_dependent=bool(data.get("is_weather_dependent", False)),
            address=str(data.get("address", "")),
            time_slot=str(data.get("time_slot", "flessibile")),
            cost_info=data.get("cost_info"),
            is_free=bool(data.get("is_free", False)),
            tags=list(data.get("tags", [])),
            raw_metadata=dict(data.get("raw_metadata", {})),
        )


@dataclass
class WeeklyCatalog:
    """Container for the weekly catalog of verified outings."""
    week_label: str
    generated_at: str
    activities: List[OutingOption] = field(default_factory=list)

    def filter_by_category(self, category: OutingCategory | str | None) -> List[OutingOption]:
        """Return subset of activities matching the given category.
        If category is None or empty string, returns all activities.
        """
        if category is None or category == "":
            return list(self.activities)
        if isinstance(category, OutingCategory):
            target = category.value
        else:
            target = OutingCategory.from_str(str(category)).value
        return [act for act in self.activities if act.category.value == target]

    def to_dict(self) -> Dict[str, Any]:
        """Convert WeeklyCatalog to serializable dictionary."""
        return {
            "week_label": self.week_label,
            "generated_at": self.generated_at,
            "activities": [a.to_dict() for a in self.activities],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WeeklyCatalog:
        """Construct WeeklyCatalog from dictionary."""
        activities = [OutingOption.from_dict(item) for item in data.get("activities", [])]
        return cls(
            week_label=str(data.get("week_label", "")),
            generated_at=str(data.get("generated_at", "")),
            activities=activities,
        )
