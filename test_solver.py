"""
Unit tests for the Ship Crew Optimizer solver engine.

Tests cover:
- Data model serialization/deserialization
- Base stat calculation
- Percentage multiplier application
- Final stat calculation with floor
- Combination generation
- Voyage target filtering
- Result ranking
"""

import unittest
import json
import math
import tempfile
import os

from models import (
    Stats, Captain, CrewMember, ShipPart,
    BuildingBonuses, ConsumableBuff, VoyageTarget,
    Roster, ShipConfig
)
from solver import (
    calculate_base_stats,
    calculate_percentage_multipliers,
    calculate_final_stats,
    generate_combinations,
    meets_voyage_targets,
    calculate_composite_score,
    optimize,
    get_best_assignment,
    CrewAssignment,
    OptimizationResult
)


class TestStats(unittest.TestCase):
    """Tests for the Stats dataclass."""

    def test_stats_creation(self):
        """Test creating a Stats object with default values."""
        stats = Stats()
        self.assertEqual(stats.morale, 0)
        self.assertEqual(stats.combat, 0)
        self.assertEqual(stats.seafaring, 0)

    def test_stats_creation_with_values(self):
        """Test creating a Stats object with specific values."""
        stats = Stats(morale=10, combat=20, seafaring=30)
        self.assertEqual(stats.morale, 10)
        self.assertEqual(stats.combat, 20)
        self.assertEqual(stats.seafaring, 30)

    def test_stats_addition(self):
        """Test adding two Stats objects."""
        s1 = Stats(morale=10, combat=20, seafaring=30)
        s2 = Stats(morale=5, combat=10, seafaring=15)
        result = s1 + s2
        self.assertEqual(result.morale, 15)
        self.assertEqual(result.combat, 30)
        self.assertEqual(result.seafaring, 45)

    def test_stats_to_dict(self):
        """Test converting Stats to dictionary."""
        stats = Stats(morale=10, combat=20, seafaring=30)
        d = stats.to_dict()
        self.assertEqual(d, {'morale': 10, 'combat': 20, 'seafaring': 30})

    def test_stats_from_dict(self):
        """Test creating Stats from dictionary."""
        d = {'morale': 10, 'combat': 20, 'seafaring': 30}
        stats = Stats.from_dict(d)
        self.assertEqual(stats.morale, 10)
        self.assertEqual(stats.combat, 20)
        self.assertEqual(stats.seafaring, 30)

    def test_stats_getitem(self):
        """Test dictionary-style access to stats."""
        stats = Stats(morale=10, combat=20, seafaring=30)
        self.assertEqual(stats['morale'], 10)
        self.assertEqual(stats['combat'], 20)
        self.assertEqual(stats['seafaring'], 30)


class TestCaptain(unittest.TestCase):
    """Tests for the Captain dataclass."""

    def test_captain_creation(self):
        """Test creating a Captain object."""
        captain = Captain(name="Blackbeard", base_stats=Stats(morale=10, combat=20, seafaring=15))
        self.assertEqual(captain.name, "Blackbeard")
        self.assertEqual(captain.base_stats.morale, 10)
        self.assertEqual(captain.current_stats.morale, 10)

    def test_captain_with_traits(self):
        """Test creating a Captain with traits."""
        captain = Captain(
            name="Admiral Nelson",
            base_stats=Stats(morale=15, combat=25, seafaring=20),
            traits=['Leader', 'Tactician']
        )
        self.assertEqual(len(captain.traits), 2)
        self.assertIn('Leader', captain.traits)
        self.assertIn('Tactician', captain.traits)

    def test_captain_serialization(self):
        """Test Captain to_dict and from_dict."""
        captain = Captain(
            name="Captain Hook",
            base_stats=Stats(morale=12, combat=18, seafaring=22),
            traits=['Seafriend']
        )
        d = captain.to_dict()
        restored = Captain.from_dict(d)
        self.assertEqual(restored.name, captain.name)
        self.assertEqual(restored.base_stats.morale, captain.base_stats.morale)
        self.assertEqual(restored.base_stats.combat, captain.base_stats.combat)
        self.assertEqual(restored.base_stats.seafaring, captain.base_stats.seafaring)
        self.assertEqual(restored.traits, captain.traits)


class TestCrewMember(unittest.TestCase):
    """Tests for the CrewMember dataclass."""

    def test_crew_member_creation(self):
        """Test creating a CrewMember object."""
        crew = CrewMember(name="Sailor Jack", base_stats=Stats(morale=5, combat=8, seafaring=10))
        self.assertEqual(crew.name, "Sailor Jack")
        self.assertEqual(crew.base_stats.combat, 8)
        self.assertEqual(crew.current_stats.combat, 8)

    def test_crew_member_serialization(self):
        """Test CrewMember to_dict and from_dict."""
        crew = CrewMember(name="Boatswone Smith", base_stats=Stats(morale=7, combat=12, seafaring=15))
        d = crew.to_dict()
        restored = CrewMember.from_dict(d)
        self.assertEqual(restored.name, crew.name)
        self.assertEqual(restored.base_stats, crew.base_stats)


class TestShipPart(unittest.TestCase):
    """Tests for the ShipPart dataclass."""

    def test_ship_part_creation(self):
        """Test creating a ShipPart with default values."""
        part = ShipPart(name="Test Part")
        self.assertEqual(part.name, "Test Part")
        self.assertEqual(part.morale, 0)
        self.assertEqual(part.combat, 0)
        self.assertEqual(part.seafaring, 0)

    def test_ship_part_with_values(self):
        """Test creating a ShipPart with stat values."""
        part = ShipPart(name="Battle Hull", morale=200, combat=450, seafaring=200)
        self.assertEqual(part.name, "Battle Hull")
        self.assertEqual(part.morale, 200)
        self.assertEqual(part.combat, 450)
        self.assertEqual(part.seafaring, 200)

    def test_ship_part_serialization(self):
        """Test ShipPart to_dict and from_dict."""
        part = ShipPart(name="Golden Hull", morale=450, combat=200, seafaring=200)
        d = part.to_dict()
        restored = ShipPart.from_dict(d)
        self.assertEqual(restored.name, part.name)
        self.assertEqual(restored.morale, part.morale)
        self.assertEqual(restored.combat, part.combat)
        self.assertEqual(restored.seafaring, part.seafaring)


class TestBuildingBonuses(unittest.TestCase):
    """Tests for the BuildingBonuses dataclass."""

    def test_building_bonuses_creation(self):
        """Test creating BuildingBonuses with default values."""
        bonuses = BuildingBonuses()
        self.assertEqual(bonuses.morale, 0.0)
        self.assertEqual(bonuses.combat, 0.0)
        self.assertEqual(bonuses.seafaring, 0.0)

    def test_building_bonuses_addition(self):
        """Test adding BuildingBonuses (cumulative)."""
        b1 = BuildingBonuses(morale=0.10, combat=0.05, seafaring=0.0)
        b2 = BuildingBonuses(morale=0.05, combat=0.10, seafaring=0.05)
        result = b1 + b2
        self.assertAlmostEqual(result.morale, 0.15, places=9)
        self.assertAlmostEqual(result.combat, 0.15, places=9)
        self.assertAlmostEqual(result.seafaring, 0.05, places=9)


class TestShipwrightBonuses(unittest.TestCase):
    """Tests for the shipwright building bonuses function."""

    def test_dilapidated_no_bonus(self):
        """Test Dilapidated Shipwright gives no bonus."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Dilapidated Shipwright")
        self.assertEqual(bonuses.morale, 0.0)
        self.assertEqual(bonuses.combat, 0.0)
        self.assertEqual(bonuses.seafaring, 0.0)

    def test_refitted_2_percent(self):
        """Test Refitted Shipwright gives +2% all stats."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Refitted Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.02, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.02, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.02, places=9)

    def test_nautical_bonus(self):
        """Test Nautical Shipwright gives +3% all +2% seafaring."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Nautical Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.03, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.03, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.05, places=9)

    def test_warship_bonus(self):
        """Test Warship Shipwright gives +3% all +2% combat."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Warship Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.03, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.05, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.03, places=9)

    def test_luxurious_bonus(self):
        """Test Luxurious Shipwright gives +3% all +2% morale."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Luxurious Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.05, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.03, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.03, places=9)

    def test_ostentatious_bonus(self):
        """Test Ostentatious Shipwright gives +5% all +3% morale."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Ostentatious Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.08, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.05, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.05, places=9)

    def test_battleship_bonus(self):
        """Test Battleship Shipwright gives +5% all +3% combat."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Battleship Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.05, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.08, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.05, places=9)

    def test_maritime_bonus(self):
        """Test Maritime Shipwright gives +5% all +3% seafaring."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Maritime Shipwright")
        self.assertAlmostEqual(bonuses.morale, 0.05, places=9)
        self.assertAlmostEqual(bonuses.combat, 0.05, places=9)
        self.assertAlmostEqual(bonuses.seafaring, 0.08, places=9)

    def test_unknown_type_returns_zero(self):
        """Test unknown shipwright type returns zero bonuses."""
        from models import get_shipwright_bonuses
        bonuses = get_shipwright_bonuses("Unknown Type")
        self.assertEqual(bonuses.morale, 0.0)
        self.assertEqual(bonuses.combat, 0.0)
        self.assertEqual(bonuses.seafaring, 0.0)


class TestConsumableBuff(unittest.TestCase):
    """Tests for the ConsumableBuff dataclass."""

    def test_consumable_flat_only(self):
        """Test creating a consumable with only flat stats."""
        buff = ConsumableBuff(name="Rum", flat_stats=Stats(morale=5, combat=0, seafaring=0))
        self.assertEqual(buff.name, "Rum")
        self.assertEqual(buff.flat_stats.morale, 5)
        self.assertEqual(buff.percentage_stats.morale, 0)

    def test_consumable_percentage_only(self):
        """Test creating a consumable with only percentage stats."""
        buff = ConsumableBuff(
            name="War Paint",
            percentage_stats=Stats(morale=0, combat=0.15, seafaring=0)
        )
        self.assertEqual(buff.percentage_stats.combat, 0.15)

    def test_consumable_both(self):
        """Test creating a consumable with both flat and percentage stats."""
        buff = ConsumableBuff(
            name="Elite Provisions",
            flat_stats=Stats(morale=10, combat=10, seafaring=5),
            percentage_stats=Stats(morale=0.05, combat=0.05, seafaring=0.05)
        )
        self.assertEqual(buff.flat_stats.morale, 10)
        self.assertEqual(buff.percentage_stats.combat, 0.05)

    def test_consumable_serialization(self):
        """Test ConsumableBuff to_dict and from_dict."""
        buff = ConsumableBuff(
            name="Cannon Balls",
            flat_stats=Stats(morale=0, combat=8, seafaring=0),
            percentage_stats=Stats(morale=0, combat=0.10, seafaring=0)
        )
        d = buff.to_dict()
        restored = ConsumableBuff.from_dict(d)
        self.assertEqual(restored.name, buff.name)
        self.assertEqual(restored.flat_stats.combat, buff.flat_stats.combat)
        self.assertEqual(restored.percentage_stats.combat, buff.percentage_stats.combat)


class TestVoyageTarget(unittest.TestCase):
    """Tests for the VoyageTarget dataclass."""

    def test_voyage_target_creation(self):
        """Test creating VoyageTarget."""
        target = VoyageTarget(morale=50, combat=100, seafaring=75)
        self.assertEqual(target.morale, 50)
        self.assertEqual(target.combat, 100)
        self.assertEqual(target.seafaring, 75)

    def test_voyage_target_serialization(self):
        """Test VoyageTarget to_dict and from_dict."""
        target = VoyageTarget(morale=50, combat=100, seafaring=75)
        d = target.to_dict()
        restored = VoyageTarget.from_dict(d)
        self.assertEqual(restored, target)


class TestRoster(unittest.TestCase):
    """Tests for the Roster dataclass."""

    def test_roster_serialization(self):
        """Test Roster to_dict and from_dict."""
        roster = Roster(
            captains=[Captain(name="Captain A", base_stats=Stats(morale=10, combat=20, seafaring=15))],
            crew=[CrewMember(name="Crew B", base_stats=Stats(morale=5, combat=10, seafaring=8))]
        )
        d = roster.to_dict()
        restored = Roster.from_dict(d)
        self.assertEqual(len(restored.captains), 1)
        self.assertEqual(len(restored.crew), 1)
        self.assertEqual(restored.captains[0].name, "Captain A")
        self.assertEqual(restored.crew[0].name, "Crew B")

    def test_roster_file_io(self):
        """Test saving and loading roster to/from file."""
        roster = Roster(
            captains=[Captain(name="File Captain", base_stats=Stats(morale=15, combat=25, seafaring=20))],
            crew=[CrewMember(name="File Crew", base_stats=Stats(morale=8, combat=12, seafaring=10))]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            roster.save_to_file(temp_path)
            loaded = Roster.load_from_file(temp_path)
            self.assertEqual(len(loaded.captains), 1)
            self.assertEqual(loaded.captains[0].name, "File Captain")
            self.assertEqual(len(loaded.crew), 1)
            self.assertEqual(loaded.crew[0].name, "File Crew")
        finally:
            os.unlink(temp_path)


class TestShipConfig(unittest.TestCase):
    """Tests for the ShipConfig dataclass."""

    def test_ship_config_serialization(self):
        """Test ShipConfig to_dict and from_dict."""
        config = ShipConfig(
            ship_name="HMS Victory",
            active_building_bonuses=BuildingBonuses(morale=0.10, combat=0.05, seafaring=0.0),
            active_consumables=[ConsumableBuff(name="Rum", flat_stats=Stats(morale=5, combat=0, seafaring=0))]
        )
        # Set up equipment
        config.set_equipment('Hull', ShipPart(name="Battle Hull", morale=100, combat=200, seafaring=50))
        d = config.to_dict()
        restored = ShipConfig.from_dict(d)
        self.assertEqual(restored.ship_name, "HMS Victory")
        self.assertEqual(restored.get_equipment_stats().combat, 200)
        self.assertEqual(restored.active_building_bonuses.morale, 0.10)
        self.assertEqual(len(restored.active_consumables), 1)

    def test_ship_config_file_io(self):
        """Test saving and loading ship config to/from file."""
        config = ShipConfig(
            ship_name="Test Ship"
        )
        config.set_equipment('Deck Item 1', ShipPart(name="Cannon x2", morale=0, combat=450, seafaring=0))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            config.save_to_file(temp_path)
            loaded = ShipConfig.load_from_file(temp_path)
            self.assertEqual(loaded.ship_name, "Test Ship")
            self.assertEqual(loaded.get_equipment_stats().combat, 450)
        finally:
            os.unlink(temp_path)


class TestCalculateBaseStats(unittest.TestCase):
    """Tests for base stat calculation."""

    def test_base_stats_minimal(self):
        """Test base stats with only captain."""
        captain = Captain(name="Solo Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        ship_config = ShipConfig(ship_name="Test Ship")
        result = calculate_base_stats(captain, [], ship_config, [])
        self.assertEqual(result.morale, 10)
        self.assertEqual(result.combat, 20)
        self.assertEqual(result.seafaring, 15)

    def test_base_stats_with_crew(self):
        """Test base stats with captain and crew."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        crew1 = CrewMember(name="Crew1", base_stats=Stats(morale=5, combat=10, seafaring=8))
        crew2 = CrewMember(name="Crew2", base_stats=Stats(morale=3, combat=7, seafaring=12))
        ship_config = ShipConfig(ship_name="Test Ship")
        result = calculate_base_stats(captain, [crew1, crew2], ship_config, [])
        self.assertEqual(result.morale, 18)  # 10 + 5 + 3
        self.assertEqual(result.combat, 37)   # 20 + 10 + 7
        self.assertEqual(result.seafaring, 35)  # 15 + 8 + 12

    def test_base_stats_with_equipment(self):
        """Test base stats with ship equipment."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        ship_config = ShipConfig(ship_name="Test Ship")
        ship_config.set_equipment('Hull', ShipPart(name="Battle Hull", morale=5, combat=10, seafaring=5))
        result = calculate_base_stats(captain, [], ship_config, [])
        self.assertEqual(result.morale, 15)
        self.assertEqual(result.combat, 30)
        self.assertEqual(result.seafaring, 20)

    def test_base_stats_with_flat_consumables(self):
        """Test base stats with flat consumable bonuses."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        consumable = ConsumableBuff(name="Rations", flat_stats=Stats(morale=5, combat=3, seafaring=2))
        ship_config = ShipConfig(ship_name="Test Ship")
        result = calculate_base_stats(captain, [], ship_config, [consumable])
        self.assertEqual(result.morale, 15)
        self.assertEqual(result.combat, 23)
        self.assertEqual(result.seafaring, 17)


class TestCalculatePercentageMultipliers(unittest.TestCase):
    """Tests for percentage multiplier calculation."""

    def test_no_multipliers(self):
        """Test with no percentage sources."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        result = calculate_percentage_multipliers(captain, BuildingBonuses(), [])
        self.assertEqual(result.morale, 0.0)
        self.assertEqual(result.combat, 0.0)
        self.assertEqual(result.seafaring, 0.0)

    def test_building_bonuses_only(self):
        """Test with only building bonuses."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        buildings = BuildingBonuses(morale=0.10, combat=0.15, seafaring=0.05)
        result = calculate_percentage_multipliers(captain, buildings, [])
        self.assertEqual(result.morale, 0.10)
        self.assertEqual(result.combat, 0.15)
        self.assertEqual(result.seafaring, 0.05)

    def test_captain_traits(self):
        """Test with captain traits."""
        captain = Captain(
            name="Admiral",
            base_stats=Stats(morale=10, combat=20, seafaring=15),
            traits=['Tactician', 'Leader']
        )
        result = calculate_percentage_multipliers(captain, BuildingBonuses(), [])
        # Tactician trait: +0.01 combat, Leader trait: +0.01 morale
        self.assertAlmostEqual(result.morale, 0.01, places=9)
        self.assertAlmostEqual(result.combat, 0.01, places=9)
        self.assertAlmostEqual(result.seafaring, 0.0, places=9)

    def test_percentage_consumables(self):
        """Test with percentage consumables."""
        captain = Captain(name="Captain", base_stats=Stats(morale=10, combat=20, seafaring=15))
        consumable = ConsumableBuff(
            name="War Brew",
            percentage_stats=Stats(morale=0.05, combat=0.10, seafaring=0.05)
        )
        result = calculate_percentage_multipliers(captain, BuildingBonuses(), [consumable])
        self.assertEqual(result.morale, 0.05)
        self.assertEqual(result.combat, 0.10)
        self.assertEqual(result.seafaring, 0.05)

    def test_combined_multipliers(self):
        """Test with all percentage sources combined."""
        captain = Captain(
            name="Admiral",
            base_stats=Stats(morale=10, combat=20, seafaring=15),
            traits=['Seafriend']
        )
        buildings = BuildingBonuses(morale=0.10, combat=0.10, seafaring=0.10)
        consumable = ConsumableBuff(
            name="Buff",
            percentage_stats=Stats(morale=0.05, combat=0.05, seafaring=0.05)
        )
        result = calculate_percentage_multipliers(captain, buildings, [consumable])
        # morale: 0.10 (building) + 0.05 (consumable) = 0.15
        # combat: 0.10 (building) + 0.05 (consumable) = 0.15
        # seafaring: 0.01 (Seafriend trait) + 0.10 (building) + 0.05 (consumable) = 0.16
        self.assertAlmostEqual(result.morale, 0.15, places=9)
        self.assertAlmostEqual(result.combat, 0.15, places=9)
        self.assertAlmostEqual(result.seafaring, 0.16, places=9)


class TestCalculateFinalStats(unittest.TestCase):
    """Tests for final stat calculation with floor."""

    def test_no_multiplier(self):
        """Test with no multipliers (should return floor of base)."""
        base = Stats(morale=10, combat=20, seafaring=30)
        multipliers = Stats(morale=0, combat=0, seafaring=0)
        result = calculate_final_stats(base, multipliers)
        self.assertEqual(result.morale, 10)
        self.assertEqual(result.combat, 20)
        self.assertEqual(result.seafaring, 30)

    def test_with_multiplier(self):
        """Test with percentage multipliers."""
        base = Stats(morale=100, combat=100, seafaring=100)
        multipliers = Stats(morale=0.10, combat=0.20, seafaring=0.15)
        result = calculate_final_stats(base, multipliers)
        self.assertEqual(result.morale, 110)  # floor(100 * 1.10)
        self.assertEqual(result.combat, 120)   # floor(100 * 1.20)
        self.assertEqual(result.seafaring, 115)  # floor(100 * 1.15) = 115.0 rounded = 115

    def test_floor_behavior(self):
        """Test that floor is applied correctly."""
        base = Stats(morale=33, combat=33, seafaring=33)
        multipliers = Stats(morale=0.10, combat=0.10, seafaring=0.10)
        result = calculate_final_stats(base, multipliers)
        # floor(33 * 1.10) = floor(36.3) = 36
        self.assertEqual(result.morale, 36)
        self.assertEqual(result.combat, 36)
        self.assertEqual(result.seafaring, 36)

    def test_fractional_base(self):
        """Test with fractional results that need flooring."""
        base = Stats(morale=10, combat=10, seafaring=10)
        multipliers = Stats(morale=0.15, combat=0.25, seafaring=0.33)
        result = calculate_final_stats(base, multipliers)
        # floor(10 * 1.15) = floor(11.5) = 11
        # floor(10 * 1.25) = floor(12.5) = 12
        # floor(10 * 1.33) = floor(13.3) = 13
        self.assertEqual(result.morale, 11)
        self.assertEqual(result.combat, 12)
        self.assertEqual(result.seafaring, 13)


class TestGenerateCombinations(unittest.TestCase):
    """Tests for combination generation."""

    def test_no_crew(self):
        """Test with no crew members available."""
        captains = [Captain(name="Captain A", base_stats=Stats())]
        result = generate_combinations(captains, [], max_crew=5)
        # Only one combination: captain alone
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0].name, "Captain A")
        self.assertEqual(len(result[0][1]), 0)

    def test_fewer_crew_than_max(self):
        """Test with fewer crew than max_crew."""
        captains = [Captain(name="Captain A", base_stats=Stats())]
        crew = [
            CrewMember(name="Crew1", base_stats=Stats()),
            CrewMember(name="Crew2", base_stats=Stats())
        ]
        result = generate_combinations(captains, crew, max_crew=5)
        # 1 (alone) + 2 (1 crew) + 1 (2 crew) = 4
        expected = 1 + 2 + 1
        self.assertEqual(len(result), expected)

    def test_multiple_captains(self):
        """Test with multiple captains."""
        captains = [
            Captain(name="Captain A", base_stats=Stats()),
            Captain(name="Captain B", base_stats=Stats())
        ]
        crew = [CrewMember(name="Crew1", base_stats=Stats())]
        result = generate_combinations(captains, crew, max_crew=5)
        # 2 captains * (1 alone + 1 with crew) = 4
        self.assertEqual(len(result), 4)

    def test_max_crew_limit(self):
        """Test that max_crew limit is respected."""
        captains = [Captain(name="Captain A", base_stats=Stats())]
        crew = [CrewMember(name=f"Crew{i}", base_stats=Stats()) for i in range(10)]
        result = generate_combinations(captains, crew, max_crew=2)
        # 1 (alone) + 10 (1 crew) + 45 (2 crew) = 56
        expected = 1 + 10 + 45
        self.assertEqual(len(result), expected)


class TestMeetsVoyageTargets(unittest.TestCase):
    """Tests for voyage target filtering."""

    def test_all_targets_met(self):
        """Test when all targets are met."""
        stats = Stats(morale=50, combat=100, seafaring=75)
        targets = VoyageTarget(morale=50, combat=100, seafaring=75)
        self.assertTrue(meets_voyage_targets(stats, targets))

    def test_one_target_met(self):
        """Test when one stat is below target."""
        stats = Stats(morale=49, combat=100, seafaring=75)
        targets = VoyageTarget(morale=50, combat=100, seafaring=75)
        self.assertFalse(meets_voyage_targets(stats, targets))

    def test_all_targets_exceeded(self):
        """Test when all stats exceed targets."""
        stats = Stats(morale=60, combat=110, seafaring=80)
        targets = VoyageTarget(morale=50, combat=100, seafaring=75)
        self.assertTrue(meets_voyage_targets(stats, targets))

    def test_zero_targets(self):
        """Test with zero targets (any stats should pass)."""
        stats = Stats(morale=0, combat=0, seafaring=0)
        targets = VoyageTarget(morale=0, combat=0, seafaring=0)
        self.assertTrue(meets_voyage_targets(stats, targets))


class TestCalculateCompositeScore(unittest.TestCase):
    """Tests for composite score calculation."""

    def test_exact_match(self):
        """Test when stats exactly match targets (score = 1.0)."""
        stats = Stats(morale=50, combat=100, seafaring=75)
        targets = VoyageTarget(morale=50, combat=100, seafaring=75)
        score = calculate_composite_score(stats, targets)
        self.assertEqual(score, 1.0)

    def test_exceeding_targets(self):
        """Test when stats exceed targets (score > 1.0)."""
        stats = Stats(morale=100, combat=200, seafaring=150)
        targets = VoyageTarget(morale=50, combat=100, seafaring=75)
        score = calculate_composite_score(stats, targets)
        self.assertEqual(score, 2.0)  # All stats are 2x target

    def test_below_targets(self):
        """Test when stats are below targets (score < 1.0)."""
        stats = Stats(morale=25, combat=50, seafaring=37)
        targets = VoyageTarget(morale=50, combat=100, seafaring=74)
        score = calculate_composite_score(stats, targets)
        # morale: 25/50 = 0.5, combat: 50/100 = 0.5, seafaring: 37/74 = 0.5
        # score = (0.5 + 0.5 + 0.5) / 3 = 0.5
        self.assertAlmostEqual(score, 0.5, places=9)

    def test_zero_targets(self):
        """Test with zero targets (uses raw stat values)."""
        stats = Stats(morale=10, combat=20, seafaring=30)
        targets = VoyageTarget(morale=0, combat=0, seafaring=0)
        score = calculate_composite_score(stats, targets)
        self.assertEqual(score, 20.0)  # (10 + 20 + 30) / 3


class TestOptimize(unittest.TestCase):
    """Integration tests for the optimize function."""

    def test_basic_optimization(self):
        """Test basic optimization with simple data."""
        captains = [
            Captain(name="Captain A", base_stats=Stats(morale=20, combat=30, seafaring=25)),
            Captain(name="Captain B", base_stats=Stats(morale=25, combat=25, seafaring=30))
        ]
        crew = [
            CrewMember(name="Crew1", base_stats=Stats(morale=10, combat=15, seafaring=12)),
            CrewMember(name="Crew2", base_stats=Stats(morale=8, combat=12, seafaring=15)),
            CrewMember(name="Crew3", base_stats=Stats(morale=12, combat=10, seafaring=8))
        ]
        ship_config = ShipConfig(
            ship_name="Test Ship",
            active_building_bonuses=BuildingBonuses(morale=0.10, combat=0.05, seafaring=0.0),
            active_consumables=[ConsumableBuff(name="Rum", flat_stats=Stats(morale=5, combat=0, seafaring=0))]
        )
        ship_config.set_equipment('Hull', ShipPart(name="Battle Hull", morale=5, combat=10, seafaring=5))
        targets = VoyageTarget(morale=50, combat=100, seafaring=70)

        results = optimize(captains, crew, ship_config, targets, max_crew=5)

        self.assertGreater(len(results), 0)
        # Results should be sorted by composite_score descending
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].composite_score,
                results[i + 1].composite_score
            )

    def test_optimization_with_no_valid_results(self):
        """Test optimization when no combination meets targets."""
        captains = [
            Captain(name="Weak Captain", base_stats=Stats(morale=1, combat=1, seafaring=1))
        ]
        crew = [
            CrewMember(name="Weak Crew", base_stats=Stats(morale=1, combat=1, seafaring=1))
        ]
        ship_config = ShipConfig(ship_name="Test Ship")
        targets = VoyageTarget(morale=1000, combat=1000, seafaring=1000)

        results = optimize(captains, crew, ship_config, targets, max_crew=5)

        self.assertGreater(len(results), 0)
        # No results should meet targets
        for result in results:
            self.assertFalse(result.meets_targets)

    def test_optimization_with_valid_results(self):
        """Test optimization when some combinations meet targets."""
        captains = [
            Captain(name="Strong Captain", base_stats=Stats(morale=50, combat=80, seafaring=60)),
            Captain(name="Weak Captain", base_stats=Stats(morale=5, combat=5, seafaring=5))
        ]
        crew = [
            CrewMember(name="Strong Crew", base_stats=Stats(morale=30, combat=40, seafaring=35)),
            CrewMember(name="Weak Crew", base_stats=Stats(morale=2, combat=3, seafaring=2))
        ]
        ship_config = ShipConfig(ship_name="Test Ship")
        targets = VoyageTarget(morale=80, combat=120, seafaring=90)

        results = optimize(captains, crew, ship_config, targets, max_crew=5)

        self.assertGreater(len(results), 0)
        # At least one result should meet targets
        has_valid = any(r.meets_targets for r in results)
        self.assertTrue(has_valid)
        # Best result should meet targets
        self.assertTrue(results[0].meets_targets)

    def test_optimization_ranking(self):
        """Test that results are properly ranked."""
        captains = [
            Captain(name="Best Captain", base_stats=Stats(morale=50, combat=80, seafaring=60)),
            Captain(name="Middle Captain", base_stats=Stats(morale=30, combat=50, seafaring=40)),
            Captain(name="Worst Captain", base_stats=Stats(morale=10, combat=15, seafaring=10))
        ]
        crew = [
            CrewMember(name="Best Crew", base_stats=Stats(morale=30, combat=40, seafaring=35)),
            CrewMember(name="Middle Crew", base_stats=Stats(morale=15, combat=20, seafaring=15)),
            CrewMember(name="Worst Crew", base_stats=Stats(morale=5, combat=8, seafaring=5))
        ]
        ship_config = ShipConfig(ship_name="Test Ship")
        targets = VoyageTarget(morale=20, combat=30, seafaring=25)

        results = optimize(captains, crew, ship_config, targets, max_crew=5)

        self.assertGreater(len(results), 0)
        # Verify descending order
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].composite_score,
                results[i + 1].composite_score
            )


class TestGetBestAssignment(unittest.TestCase):
    """Tests for the get_best_assignment convenience function."""

    def test_get_best_returns_result(self):
        """Test that get_best_assignment returns a valid result."""
        captains = [Captain(name="Captain", base_stats=Stats(morale=20, combat=30, seafaring=25))]
        crew = [CrewMember(name="Crew", base_stats=Stats(morale=10, combat=15, seafaring=12))]
        ship_config = ShipConfig(ship_name="Test Ship")
        targets = VoyageTarget(morale=10, combat=20, seafaring=15)

        result = get_best_assignment(captains, crew, ship_config, targets)

        self.assertIsNotNone(result)
        self.assertEqual(result.assignment.captain.name, "Captain")

    def test_get_best_returns_none_when_no_captains(self):
        """Test that get_best_assignment returns None with no captains."""
        result = get_best_assignment([], [], ShipConfig(ship_name="Test Ship"), VoyageTarget())
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
