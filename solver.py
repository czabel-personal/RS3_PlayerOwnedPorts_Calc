"""
Optimization engine for ship crew assignments.

Calculates base stats, applies percentage multipliers, generates combinations,
filters by voyage targets, and ranks results.
"""

import math
import itertools
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from models import (
    Stats, Captain, CrewMember,
    BuildingBonuses, ConsumableBuff, VoyageTarget, ShipConfig
)


@dataclass
class CrewAssignment:
    """A single crew assignment with captain and crew members."""
    captain: Captain
    crew_members: List[CrewMember]
    final_stats: Stats

    def to_dict(self) -> Dict:
        """Convert assignment to dictionary."""
        return {
            'captain_name': self.captain.name,
            'crew_names': [c.name for c in self.crew_members],
            'final_stats': self.final_stats.to_dict()
        }


@dataclass
class OptimizationResult:
    """A ranked optimization result."""
    assignment: CrewAssignment
    composite_score: float
    meets_targets: bool

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            'assignment': self.assignment.to_dict(),
            'composite_score': self.composite_score,
            'meets_targets': self.meets_targets
        }


def calculate_base_stats(
    captain: Captain,
    crew_members: List[CrewMember],
    ship_config: ShipConfig,
    flat_consumables: List[ConsumableBuff]
) -> Stats:
    """
    Calculate the base sum of stats from:
    - 1 Captain
    - Up to 5 Crew members
    - Ship equipment (flat bonuses from ShipPart slots)
    - Consumable flat bonuses

    Returns: Summed Stats object
    """
    # Sum captain stats
    total = captain.current_stats

    # Sum crew stats
    for crew in crew_members:
        total = total + crew.current_stats

    # Add ship equipment stats (flat bonuses from equipped ShipParts)
    total = total + ship_config.get_equipment_stats()

    # Add flat consumable bonuses
    for consumable in flat_consumables:
        total = total + consumable.flat_stats

    return total


def calculate_percentage_multipliers(
    captain: Captain,
    building_bonuses: BuildingBonuses,
    percentage_consumables: List[ConsumableBuff]
) -> Stats:
    """
    Calculate the total percentage multipliers from:
    - Captain traits (Leader: +1% morale, Tactician: +1% combat, Seafriend: +1% seafaring)
    - Building bonuses
    - Consumable percentage bonuses

    Returns: Stats object with percentage values (as decimals)
    """
    # Start with building bonuses
    total = Stats(
        morale=building_bonuses.morale,
        combat=building_bonuses.combat,
        seafaring=building_bonuses.seafaring
    )

    # Add captain traits (each trait gives +1% = 0.01 to the relevant stat)
    for trait in captain.traits:
        if trait == 'Leader':
            total = Stats(morale=total.morale + 0.01, combat=total.combat, seafaring=total.seafaring)
        elif trait == 'Tactician':
            total = Stats(morale=total.morale, combat=total.combat + 0.01, seafaring=total.seafaring)
        elif trait == 'Seafriend':
            total = Stats(morale=total.morale, combat=total.combat, seafaring=total.seafaring + 0.01)

    # Add percentage consumable bonuses
    for consumable in percentage_consumables:
        total = Stats(
            morale=total.morale + consumable.percentage_stats.morale,
            combat=total.combat + consumable.percentage_stats.combat,
            seafaring=total.seafaring + consumable.percentage_stats.seafaring
        )

    return total


def calculate_final_stats(base_stats: Stats, multipliers: Stats) -> Stats:
    """
    Calculate final stats using the formula:
    final_stat = floor(base_sum * (1 + sum_of_percent_multipliers))

    Uses rounding before floor to handle floating-point precision issues.

    Returns: Stats object with final calculated values
    """
    return Stats(
        morale=math.floor(round(base_stats.morale * (1 + multipliers.morale), 10)),
        combat=math.floor(round(base_stats.combat * (1 + multipliers.combat), 10)),
        seafaring=math.floor(round(base_stats.seafaring * (1 + multipliers.seafaring), 10))
    )


def generate_combinations(
    captains: List[Captain],
    crew: List[CrewMember],
    max_crew: int = 5
) -> List[Tuple[Captain, List[CrewMember]]]:
    """
    Generate all valid combinations of 1 captain + up to max_crew crew members.

    Returns: List of (Captain, [CrewMember, ...]) tuples
    """
    combinations = []

    for captain in captains:
        # Generate combinations for each possible crew size (0 to max_crew)
        for crew_size in range(0, min(max_crew, len(crew)) + 1):
            if crew_size == 0:
                # Captain alone
                combinations.append((captain, []))
            else:
                for crew_combo in itertools.combinations(crew, crew_size):
                    combinations.append((captain, list(crew_combo)))

    return combinations


def meets_voyage_targets(final_stats: Stats, targets: VoyageTarget) -> bool:
    """
    Check if final stats meet all voyage target requirements.

    Returns: True if all stats meet or exceed targets
    """
    return (
        final_stats.morale >= targets.morale and
        final_stats.combat >= targets.combat and
        final_stats.seafaring >= targets.seafaring
    )


def calculate_composite_score(final_stats: Stats, targets: VoyageTarget) -> float:
    """
    Calculate a composite score for ranking results.
    Uses weighted average of percentage-over-target for each stat.

    Formula: score = (morale_pct + combat_pct + seafaring_pct) / 3
    where pct = (stat / target) if target > 0 else stat

    Higher score = better result
    """
    scores = []

    if targets.morale > 0:
        scores.append(final_stats.morale / targets.morale)
    else:
        scores.append(float(final_stats.morale))

    if targets.combat > 0:
        scores.append(final_stats.combat / targets.combat)
    else:
        scores.append(float(final_stats.combat))

    if targets.seafaring > 0:
        scores.append(final_stats.seafaring / targets.seafaring)
    else:
        scores.append(float(final_stats.seafaring))

    return sum(scores) / len(scores)


def optimize(
    captains: List[Captain],
    crew: List[CrewMember],
    ship_config: ShipConfig,
    voyage_target: VoyageTarget,
    max_crew: int = 5
) -> List[OptimizationResult]:
    """
    Main optimization function.

    1. Generates all valid crew combinations
    2. Calculates base stats for each combination
    3. Applies percentage multipliers
    4. Filters by voyage targets
    5. Ranks results by composite score

    Args:
        captains: List of available captains
        crew: List of available crew members
        ship_config: Ship configuration with upgrades and bonuses
        voyage_target: Minimum stat requirements
        max_crew: Maximum number of crew members (default 5)

    Returns:
        List of OptimizationResult, sorted by composite_score descending
    """
    # Prepare flat consumables list
    flat_consumables = [c for c in ship_config.active_consumables if c.flat_stats.morale > 0 or
                        c.flat_stats.combat > 0 or c.flat_stats.seafaring > 0]
    percentage_consumables = [c for c in ship_config.active_consumables if
                              c.percentage_stats.morale > 0 or
                              c.percentage_stats.combat > 0 or
                              c.percentage_stats.seafaring > 0]

    # Generate all combinations
    combinations = generate_combinations(captains, crew, max_crew)

    results = []

    for captain, crew_members in combinations:
        # Calculate base stats
        base_stats = calculate_base_stats(
            captain,
            crew_members,
            ship_config,
            flat_consumables
        )

        # Calculate percentage multipliers
        multipliers = calculate_percentage_multipliers(
            captain,
            ship_config.active_building_bonuses,
            percentage_consumables
        )

        # Calculate final stats
        final_stats = calculate_final_stats(base_stats, multipliers)

        # Create assignment
        assignment = CrewAssignment(
            captain=captain,
            crew_members=crew_members,
            final_stats=final_stats
        )

        # Check if meets targets
        meets = meets_voyage_targets(final_stats, voyage_target)

        # Calculate composite score
        score = calculate_composite_score(final_stats, voyage_target)

        results.append(OptimizationResult(
            assignment=assignment,
            composite_score=score,
            meets_targets=meets
        ))

    # Sort by composite score descending
    results.sort(key=lambda r: r.composite_score, reverse=True)

    return results


def get_best_assignment(
    captains: List[Captain],
    crew: List[CrewMember],
    ship_config: ShipConfig,
    voyage_target: VoyageTarget,
    max_crew: int = 5
) -> Optional[OptimizationResult]:
    """
    Convenience function to get just the best optimization result.

    Returns: Best OptimizationResult or None if no valid assignment exists
    """
    results = optimize(captains, crew, ship_config, voyage_target, max_crew)

    if results:
        return results[0]
    return None
