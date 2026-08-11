"""
Data models for the Ship Crew Optimizer application.

Defines core data structures using Python dataclasses for ship crew
assignments in a naval strategy game. Includes serialization methods
for roster and ship configuration JSON files.
"""

# Design constraints - these are enforced by the GUI, not the models
MAX_CAPTAINS = 5
MAX_CREW = 25

# Valid crew types - these are enforced by the GUI, not the models
CREW_TYPES = [
    "Travelling Drunk",
    "Stowaway",
    "Smuggler",
    "Varrock Chef",
    "Brimhaven Pirate",
    "Catherby Fisherman",
    "Dwarven Engineer",
    "Ardougne Storekeeper",
    "Bamboo Golem",
    "First Mate",
    "Cyclops",
    "Eastern Bannerman",
    "Eastern Musketeer",
    "Eastern Guide",
    "Fireworks Enthusiast",
    "Palmist",
    "Exploding Golem",
    "Eastern Overseer",
    "Siren Whalerider",
    "Blazing Lantern Clansman",
    "Golden Katana Clansman",
    "Storm Riders Clansman",
    "Firework Expert",
    "Trader",
    "Soothsayer",
    "Slate Golem",
    "Feral Chimera",
    "Card Sharp",
    "Crows' Nest Sniper",
    "Cartographer",
    "Explosives Expert",
    "Merchant",
    "Cherrywood Golem",
    "Bureaucrat",
    "Sea Witch",
    "Farcrier",
    "Bounty Hunter",
    "Sea Dog",
    "Firework Maniac",
    "Jade Merchant",
    "Sacrificial Soothsayer",
    "Jade Golem",
    "Judge of Dice",
    "Travelling Band",
    "Ferocious Tiger-Rider",
    "Harem of Fortune Tellers",
    "Oxhead and Horseface",
    "Party Animal",
    "Sea-fort Guard",
    "Pearl Diver",
    "Reef Rider",
    "Terracotta Merchant",
    "Wisp",
    "Zhonghu Player",
    "Gu Bodyguard",
    "Stargazer",
    "Azure Golem",
    "Kharidian Exile"
]

# Valid shipwright building types
SHIPWRIGHT_TYPES = [
    "Dilapidated Shipwright",
    "Refitted Shipwright",
    "Renovated Shipwright",
    "Nautical Shipwright",
    "Warship Shipwright",
    "Luxurious Shipwright",
    "Sleek Shipwright",
    "Ostentatious Shipwright",
    "Battleship Shipwright",
    "Maritime Shipwright",
]

def get_shipwright_bonuses(shipwright_type: str) -> 'BuildingBonuses':
    """Calculate percentage bonuses based on shipwright building type.
    
    Based on docs/portsBuildings.txt:
    - Dilapidated Shipwright: No bonus
    - Refitted Shipwright: +2% all stats
    - Renovated Shipwright: +3% all stats
    - Nautical Shipwright: +3% all stats, +2% seafaring
    - Warship Shipwright: +3% all stats, +2% combat
    - Luxurious Shipwright: +3% all stats, +2% morale
    - Sleek Shipwright: +3% all stats, +2% speed (treated as general)
    - Ostentatious Shipwright: +5% all stats, +3% morale
    - Battleship Shipwright: +5% all stats, +3% combat
    - Maritime Shipwright: +5% all stats, +3% seafaring
    
    Args:
        shipwright_type: The name of the shipwright building type
        
    Returns:
        BuildingBonuses with the appropriate percentage bonuses
    """
    base = {
        "Dilapidated Shipwright": (0.0, 0.0, 0.0),
        "Refitted Shipwright": (0.02, 0.02, 0.02),
        "Renovated Shipwright": (0.03, 0.03, 0.03),
        "Nautical Shipwright": (0.03, 0.03, 0.05),  # +3% all, +2% seafaring
        "Warship Shipwright": (0.03, 0.05, 0.03),  # +3% all, +2% combat
        "Luxurious Shipwright": (0.05, 0.03, 0.03),  # +3% all, +2% morale
        "Sleek Shipwright": (0.03, 0.03, 0.03),  # +3% all, speed not tracked
        "Ostentatious Shipwright": (0.08, 0.05, 0.05),  # +5% all, +3% morale
        "Battleship Shipwright": (0.05, 0.08, 0.05),  # +5% all, +3% combat
        "Maritime Shipwright": (0.05, 0.05, 0.08),  # +5% all, +3% seafaring
    }
    
    morale, combat, seafaring = base.get(shipwright_type, (0.0, 0.0, 0.0))
    return BuildingBonuses(morale=morale, combat=combat, seafaring=seafaring)

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json


@dataclass
class Stats:
    """Base statistics that apply to captains and crew members."""
    morale: int = 0
    combat: int = 0
    seafaring: int = 0

    def to_dict(self) -> Dict:
        """Convert Stats to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Stats':
        """Create Stats from dictionary."""
        return cls(
            morale=data.get('morale', 0),
            combat=data.get('combat', 0),
            seafaring=data.get('seafaring', 0)
        )

    def __add__(self, other: 'Stats') -> 'Stats':
        """Add two Stats objects together."""
        return Stats(
            morale=self.morale + other.morale,
            combat=self.combat + other.combat,
            seafaring=self.seafaring + other.seafaring
        )

    def __getitem__(self, key: str) -> int:
        """Allow dictionary-style access to stats."""
        return getattr(self, key)

    def __mul__(self, factor: float) -> 'Stats':
        """Multiply stats by a factor."""
        return Stats(
            morale=int(self.morale * factor),
            combat=int(self.combat * factor),
            seafaring=int(self.seafaring * factor)
        )


@dataclass
class Captain:
    """A ship captain with base stats and optional traits.
    
    Captains start at level 1 and can level up to 10.
    Each level up increases current stats by 10% of original base stats.
    Can have up to 4 beneficial traits:
    - Leader: +1% total ship morale
    - Tactician: +1% total ship combat
    - Seafriend: +1% total ship seafaring
    """
    name: str
    base_stats: Stats
    current_stats: Stats = field(default_factory=Stats)
    level: int = 1
    traits: List[str] = field(default_factory=list)  # Up to 4 beneficial traits

    def __post_init__(self):
        """Validate captain constraints after initialization."""
        if self.level < 1 or self.level > 10:
            raise ValueError(f"Captain level must be between 1 and 10, got {self.level}")
        if len(self.traits) > 4:
            raise ValueError(f"Captain can have at most 4 traits, got {len(self.traits)}")
        valid_traits = {'Leader', 'Tactician', 'Seafriend'}
        for trait in self.traits:
            if trait not in valid_traits:
                raise ValueError(f"Invalid trait '{trait}'. Valid traits: {valid_traits}")
        # If current_stats is not set, initialize it to base_stats
        if self.current_stats.morale == 0 and self.current_stats.combat == 0 and self.current_stats.seafaring == 0:
            self.current_stats = Stats(
                morale=self.base_stats.morale,
                combat=self.base_stats.combat,
                seafaring=self.base_stats.seafaring
            )

    def level_up(self) -> bool:
        """Level up the captain by 1 level.
        
        Each level up gives +10% of original base stats to current stats.
        Returns True if leveled up successfully, False if already at max level.
        """
        if self.level >= 10:
            return False
        
        # Calculate 10% of base stats for each stat
        stat_increase = Stats(
            morale=int(self.base_stats.morale * 0.1),
            combat=int(self.base_stats.combat * 0.1),
            seafaring=int(self.base_stats.seafaring * 0.1)
        )
        
        # Add the increase to current stats
        self.current_stats = self.current_stats + stat_increase
        self.level += 1
        return True

    def to_dict(self) -> Dict:
        """Convert Captain to dictionary."""
        return {
            'name': self.name,
            'base_stats': self.base_stats.to_dict(),
            'current_stats': self.current_stats.to_dict(),
            'level': self.level,
            'traits': self.traits
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Captain':
        """Create Captain from dictionary."""
        return cls(
            name=data['name'],
            base_stats=Stats.from_dict(data.get('base_stats', {})),
            current_stats=Stats.from_dict(data.get('current_stats', {})),
            level=data.get('level', 1),
            traits=data.get('traits', [])
        )


@dataclass
class CrewMember:
    """A crew member that can be assigned to a ship.
    
    Crew members start at level 1 and can level up to 10.
    Each level up increases current stats by 10% of original base stats.
    """
    name: str
    base_stats: Stats
    current_stats: Stats = field(default_factory=Stats)
    level: int = 1

    def __post_init__(self):
        """Validate crew member constraints after initialization."""
        if self.level < 1 or self.level > 10:
            raise ValueError(f"Crew member level must be between 1 and 10, got {self.level}")
        # If current_stats is not set, initialize it to base_stats
        if self.current_stats.morale == 0 and self.current_stats.combat == 0 and self.current_stats.seafaring == 0:
            self.current_stats = Stats(
                morale=self.base_stats.morale,
                combat=self.base_stats.combat,
                seafaring=self.base_stats.seafaring
            )

    def level_up(self) -> bool:
        """Level up the crew member by 1 level.
        
        Each level up gives +10% of original base stats to current stats.
        Returns True if leveled up successfully, False if already at max level.
        """
        if self.level >= 10:
            return False
        
        # Calculate 10% of base stats for each stat
        stat_increase = Stats(
            morale=int(self.base_stats.morale * 0.1),
            combat=int(self.base_stats.combat * 0.1),
            seafaring=int(self.base_stats.seafaring * 0.1)
        )
        
        # Add the increase to current stats
        self.current_stats = self.current_stats + stat_increase
        self.level += 1
        return True

    def to_dict(self) -> Dict:
        """Convert CrewMember to dictionary."""
        return {
            'name': self.name,
            'base_stats': self.base_stats.to_dict(),
            'current_stats': self.current_stats.to_dict(),
            'level': self.level
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CrewMember':
        """Create CrewMember from dictionary."""
        return cls(
            name=data['name'],
            base_stats=Stats.from_dict(data.get('base_stats', {})),
            current_stats=Stats.from_dict(data.get('current_stats', {})),
            level=data.get('level', 1)
        )


def parse_comma_number(value) -> int:
    """Parse a number string that may contain commas (e.g., '1,200' -> 1200)."""
    if isinstance(value, int):
        return value
    return int(str(value).replace(',', ''))


@dataclass
class ShipPart:
    """A ship equipment part with its name and stat bonuses."""
    name: str
    morale: int = 0
    combat: int = 0
    seafaring: int = 0

    def to_dict(self) -> Dict:
        """Convert ShipPart to dictionary."""
        return {
            'name': self.name,
            'morale': self.morale,
            'combat': self.combat,
            'seafaring': self.seafaring
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ShipPart':
        """Create ShipPart from dictionary."""
        return cls(
            name=data['name'],
            morale=parse_comma_number(data.get('morale', 0)),
            combat=parse_comma_number(data.get('combat', 0)),
            seafaring=parse_comma_number(data.get('seafaring', 0))
        )


# Available ship parts organized by slot type
RAMS_FIGUREHEADS = [
    ShipPart("Weathered Ram", 0, 50, 0),
    ShipPart("Polished Figurehead", 100, 0, 0),
    ShipPart("Sturdy Ram", 0, 100, 0),
    ShipPart("Enchanted Figurehead", 200, 0, 0),
    ShipPart("Reinforced Ram", 0, 200, 0),
    ShipPart("Skeletal Figurehead", 350, 0, 0),
    ShipPart("Armoured Ram", 0, 350, 0),
    ShipPart("Ghostly Figurehead", 500, 0, 0),
    ShipPart("Battle Ram", 0, 500, 0),
    ShipPart("Intrepid Figurehead", 600, 0, 0),
    ShipPart("War Ram", 0, 600, 0),
    ShipPart("Inspiring Figurehead", 800, 0, 0),
    ShipPart("Spitfire Cannon", 0, 800, 0),
    ShipPart("Figurehead of the Spires", 950, 0, 100),
    ShipPart("Ram of the Bladewing", 0, 1100, 0),
]

DECK_ITEMS = [
    ShipPart("Weathered Rigging", 0, 0, 100),
    ShipPart("Small Crate of Food", 100, 0, 0),
    ShipPart("Sturdy Rigging", 0, 0, 200),
    ShipPart("Large Crate of Food", 200, 0, 0),
    ShipPart("Single Cannon", 0, 200, 0),
    ShipPart("Entwined Rigging", 0, 0, 450),
    ShipPart("Small Crate of Riches", 450, 0, 0),
    ShipPart("Cannon x2", 0, 450, 0),
    ShipPart("Oxskin Rigging", 0, 0, 700),
    ShipPart("Large Crate of Riches", 700, 0, 0),
    ShipPart("Heavy Cannon x2", 0, 700, 0),
    ShipPart("Ornate Rigging", 0, 0, 1000),
    ShipPart("Eastern Artefacts", 1000, 0, 0),
    ShipPart("Cannon x3", 0, 1000, 0),
    ShipPart("Whaleskin Rigging", 0, 0, 1200),
    ShipPart("Eastern Treasures", 1200, 0, 0),
    ShipPart("Cannon x4", 0, 1200, 0),
    ShipPart("Dragonskin Rigging", 0, 0, 1350),
    ShipPart("Eastern Relics", 1350, 0, 0),
    ShipPart("Heavy Cannon x4", 0, 1350, 0),
    ShipPart("Overwhelmingly Large Cannon x4", 0, 1750, 0),
    ShipPart("Bladewing Rigging", 0, 0, 2000),
    ShipPart("Fineglow Lanterns", 2000, 0, 0),
]

HULLS = [
    ShipPart("Barnacled Hull", 50, 50, 100),
    ShipPart("Reinforced Hull", 100, 150, 100),
    ShipPart("Sleek Hull", 100, 100, 150),
    ShipPart("Battle Hull", 200, 450, 200),
    ShipPart("Golden Hull", 450, 200, 200),
    ShipPart("Hull of Tides", 300, 300, 700),
    ShipPart("Armoured Hull", 300, 700, 300),
    ShipPart("Hull of Storms", 400, 400, 900),
    ShipPart("War Hull", 400, 900, 400),
    ShipPart("Hull of Glory", 1200, 500, 500),
    ShipPart("Storm Rider Hull", 500, 500, 1200),
    ShipPart("Golden Katana Hull", 500, 1400, 500),
    ShipPart("Blazing Lantern Hull", 1400, 500, 500),
    ShipPart("Blackwater Hull", 850, 750, 1700),
    ShipPart("Shimmering Azure Hull", 1325, 1325, 1325),
]

# Equipment slot types
EQUIPMENT_SLOTS = ['Ram/Figurehead', 'Hull', 'Deck Item 1', 'Deck Item 2']


@dataclass
class BuildingBonuses:
    """Percentage bonuses from port buildings."""
    morale: float = 0.0
    combat: float = 0.0
    seafaring: float = 0.0

    def to_dict(self) -> Dict:
        """Convert BuildingBonuses to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'BuildingBonuses':
        """Create BuildingBonuses from dictionary."""
        return cls(
            morale=data.get('morale', 0.0),
            combat=data.get('combat', 0.0),
            seafaring=data.get('seafaring', 0.0)
        )

    def __add__(self, other: 'BuildingBonuses') -> 'BuildingBonuses':
        """Add two BuildingBonuses objects together (cumulative)."""
        return BuildingBonuses(
            morale=self.morale + other.morale,
            combat=self.combat + other.combat,
            seafaring=self.seafaring + other.seafaring
        )


@dataclass
class ConsumableBuff:
    """Consumable items that provide flat or percentage bonuses."""
    name: str
    flat_stats: Stats = field(default_factory=Stats)
    percentage_stats: Stats = field(default_factory=Stats)

    def to_dict(self) -> Dict:
        """Convert ConsumableBuff to dictionary."""
        return {
            'name': self.name,
            'flat_stats': self.flat_stats.to_dict(),
            'percentage_stats': self.percentage_stats.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConsumableBuff':
        """Create ConsumableBuff from dictionary."""
        return cls(
            name=data['name'],
            flat_stats=Stats.from_dict(data.get('flat_stats', {})),
            percentage_stats=Stats.from_dict(data.get('percentage_stats', {}))
        )


@dataclass
class VoyageTarget:
    """Minimum stat requirements for a voyage."""
    morale: int = 0
    combat: int = 0
    seafaring: int = 0

    def to_dict(self) -> Dict:
        """Convert VoyageTarget to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'VoyageTarget':
        """Create VoyageTarget from dictionary."""
        return cls(
            morale=data.get('morale', 0),
            combat=data.get('combat', 0),
            seafaring=data.get('seafaring', 0)
        )


@dataclass
class Roster:
    """Complete roster containing all captains, crew members, and ships.
    
    Design constraints (enforced by GUI):
    - Max 5 captains
    - Max 25 crew members
    - Max 4 ships
    """
    captains: List[Captain] = field(default_factory=list)
    crew: List[CrewMember] = field(default_factory=list)
    ships: List['ShipConfig'] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert Roster to dictionary."""
        return {
            'captains': [c.to_dict() for c in self.captains],
            'crew': [c.to_dict() for c in self.crew],
            'ships': [s.to_dict() for s in self.ships]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Roster':
        """Create Roster from dictionary."""
        return cls(
            captains=[Captain.from_dict(c) for c in data.get('captains', [])],
            crew=[CrewMember.from_dict(c) for c in data.get('crew', [])],
            ships=[ShipConfig.from_dict(s) for s in data.get('ships', [])]
        )

    def save_to_file(self, filepath: str) -> None:
        """Save roster to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Roster':
        """Load roster from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class ShipConfig:
    """Configuration for a specific ship including equipment and active bonuses.
    
    Each ship has:
    - A customizable name (max 4 ships per roster)
    - Exactly 1 captain
    - Up to 5 regular crew members
    - 4 equipment slots: Ram/Figurehead, Hull, Deck Item 1, Deck Item 2
    """
    ship_name: str = ""
    captain: Optional[Captain] = None
    crew: List[CrewMember] = field(default_factory=list)
    equipment: Dict[str, Optional[ShipPart]] = field(default_factory=dict)
    active_building_bonuses: BuildingBonuses = field(default_factory=BuildingBonuses)
    active_consumables: List[ConsumableBuff] = field(default_factory=list)

    def __post_init__(self):
        """Initialize equipment slots and validate constraints."""
        if not self.equipment:
            self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        if len(self.crew) > 5:
            raise ValueError(f"Ship can have at most 5 crew members, got {len(self.crew)}")

    def set_equipment(self, slot: str, part: ShipPart) -> None:
        """Set a ship part in an equipment slot.
        
        Args:
            slot: Equipment slot name (Ram/Figurehead, Hull, Deck Item 1, Deck Item 2)
            part: ShipPart to equip
            
        Raises:
            ValueError: If slot is invalid
        """
        if slot not in EQUIPMENT_SLOTS:
            raise ValueError(f"Invalid equipment slot '{slot}'. Valid slots: {EQUIPMENT_SLOTS}")
        self.equipment[slot] = part

    def get_equipment_stats(self) -> Stats:
        """Get total stats from all equipped equipment."""
        total = Stats()
        for part in self.equipment.values():
            if part is not None:
                total = total + Stats(part.morale, part.combat, part.seafaring)
        return total

    def to_dict(self) -> Dict:
        """Convert ShipConfig to dictionary."""
        return {
            'ship_name': self.ship_name,
            'captain': self.captain.to_dict() if self.captain else None,
            'crew': [c.to_dict() for c in self.crew],
            'equipment': {
                slot: part.to_dict() if part else None
                for slot, part in self.equipment.items()
            },
            'active_building_bonuses': self.active_building_bonuses.to_dict(),
            'active_consumables': [c.to_dict() for c in self.active_consumables]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ShipConfig':
        """Create ShipConfig from dictionary."""
        equipment_data = data.get('equipment', {})
        equipment = {}
        for slot in EQUIPMENT_SLOTS:
            part_data = equipment_data.get(slot)
            equipment[slot] = ShipPart.from_dict(part_data) if part_data else None
        
        captain_data = data.get('captain')
        captain = Captain.from_dict(captain_data) if captain_data else None
        
        return cls(
            ship_name=data.get('ship_name', ''),
            captain=captain,
            crew=[CrewMember.from_dict(c) for c in data.get('crew', [])],
            equipment=equipment,
            active_building_bonuses=BuildingBonuses.from_dict(data.get('active_building_bonuses', {})),
            active_consumables=[ConsumableBuff.from_dict(c) for c in data.get('active_consumables', [])]
        )

    def save_to_file(self, filepath: str) -> None:
        """Save ship configuration to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'ShipConfig':
        """Load ship configuration from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
