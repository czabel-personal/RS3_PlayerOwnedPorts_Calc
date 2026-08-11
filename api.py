"""
Flask API layer for the Ship Crew Optimizer application.

Provides RESTful API endpoints for:
- Optimization requests (POST /api/optimize)
- Roster import/export (GET/POST /api/roster)
- Ship configuration import/export (GET/POST /api/ship-config)
"""

from flask import Flask, jsonify, request
import json
import os
import threading

from models import (
    Roster, ShipConfig, VoyageTarget, BuildingBonuses,
    ConsumableBuff, Captain, CrewMember, Stats,
    get_shipwright_bonuses
)
from solver import optimize, get_best_assignment, OptimizationResult

# Create Flask app
app = Flask(__name__)

# Default file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTER_FILE = os.path.join(BASE_DIR, 'roster.json')
SHIP_CONFIG_FILE = os.path.join(BASE_DIR, 'ship_config.json')


def _load_roster(filepath: str = None) -> Roster:
    """Load roster from JSON file.
    
    Returns:
        Roster object if file exists and is valid.
        None if file doesn't exist (signal to caller).
        None if file has JSON errors.
    """
    filepath = filepath or ROSTER_FILE
    if not os.path.exists(filepath):
        return None
    try:
        return Roster.load_from_file(filepath)
    except (json.JSONDecodeError, Exception) as e:
        return None  # Signal error to caller


def _save_roster(roster: Roster, filepath: str = None) -> bool:
    """Save roster to JSON file."""
    filepath = filepath or ROSTER_FILE
    try:
        roster.save_to_file(filepath)
        return True
    except Exception as e:
        return False


def _load_ship_config(filepath: str = None) -> ShipConfig:
    """Load ship configuration from JSON file, returning default on failure."""
    filepath = filepath or SHIP_CONFIG_FILE
    if not os.path.exists(filepath):
        return ShipConfig()
    try:
        return ShipConfig.load_from_file(filepath)
    except (json.JSONDecodeError, Exception) as e:
        return None


def _save_ship_config(config: ShipConfig, filepath: str = None) -> bool:
    """Save ship configuration to JSON file."""
    filepath = filepath or SHIP_CONFIG_FILE
    try:
        config.save_to_file(filepath)
        return True
    except Exception as e:
        return False


def _result_to_dict(result: OptimizationResult) -> dict:
    """Convert an OptimizationResult to a dictionary for JSON serialization."""
    return {
        'assignment': {
            'captain_name': result.assignment.captain.name,
            'captain_level': result.assignment.captain.level,
            'captain_stats': result.assignment.captain.current_stats.to_dict(),
            'crew_members': [
                {
                    'name': c.name,
                    'level': c.level,
                    'stats': c.current_stats.to_dict()
                }
                for c in result.assignment.crew_members
            ],
            'final_stats': result.assignment.final_stats.to_dict()
        },
        'composite_score': round(result.composite_score, 4),
        'meets_targets': result.meets_targets
    }


# =============================================================================
# Optimization Endpoint
# =============================================================================

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    """
    Submit voyage targets and receive optimized crew assignments.
    
    Expected JSON body:
    {
        "voyage_target": {
            "morale": 100,
            "combat": 150,
            "seafaring": 120
        },
        "building_bonuses": {
            "morale": 0.03,
            "combat": 0.03,
            "seafaring": 0.05
        },
        "consumables": [
            {
                "name": "Sample Consumable",
                "flat_stats": {"morale": 10, "combat": 0, "seafaring": 0},
                "percentage_stats": {"morale": 0.0, "combat": 0.0, "seafaring": 0.0}
            }
        ],
        "shipwright_type": "Maritime Shipwright",
        "max_results": 10
    }
    
    Returns:
    {
        "success": true,
        "results": [...],
        "total_combinations": 500
    }
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"success": False, "error": "Invalid or missing JSON body"}), 400

        # Parse voyage target
        target_data = data.get('voyage_target', {})
        voyage_target = VoyageTarget(
            morale=target_data.get('morale', 0),
            combat=target_data.get('combat', 0),
            seafaring=target_data.get('seafaring', 0)
        )

        # Parse building bonuses
        # Can be provided directly or derived from shipwright_type
        shipwright_type = data.get('shipwright_type')
        if shipwright_type:
            building_bonuses = get_shipwright_bonuses(shipwright_type)
        else:
            bonus_data = data.get('building_bonuses', {})
            building_bonuses = BuildingBonuses(
                morale=bonus_data.get('morale', 0.0),
                combat=bonus_data.get('combat', 0.0),
                seafaring=bonus_data.get('seafaring', 0.0)
            )

        # Parse consumables
        consumables_data = data.get('consumables', [])
        consumables = []
        for c in consumables_data:
            flat = c.get('flat_stats', {})
            pct = c.get('percentage_stats', {})
            consumables.append(ConsumableBuff(
                name=c.get('name', ''),
                flat_stats=Stats(
                    morale=flat.get('morale', 0),
                    combat=flat.get('combat', 0),
                    seafaring=flat.get('seafaring', 0)
                ),
                percentage_stats=Stats(
                    morale=pct.get('morale', 0.0),
                    combat=pct.get('combat', 0.0),
                    seafaring=pct.get('seafaring', 0.0)
                )
            ))

        max_results = data.get('max_results', 10)

        # Get captains and crew from the roster file
        roster = _load_roster()
        if roster is None:
            return jsonify({"success": False, "error": "Could not load roster. Ensure roster.json exists."}), 404

        captains = roster.captains
        crew = roster.crew

        if not captains:
            return jsonify({"success": False, "error": "No captains found in roster"}), 400
        if not crew:
            return jsonify({"success": False, "error": "No crew members found in roster"}), 400

        # Create a temporary ship config for optimization
        temp_config = ShipConfig(
            active_building_bonuses=building_bonuses,
            active_consumables=consumables
        )

        # Run optimization
        results = optimize(
            captains=captains,
            crew=crew,
            ship_config=temp_config,
            voyage_target=voyage_target,
            max_crew=5
        )

        # Limit results
        limited_results = results[:max_results]

        # Convert to serializable format
        result_dicts = [_result_to_dict(r) for r in limited_results]

        return jsonify({
            "success": True,
            "results": result_dicts,
            "total_combinations": len(results)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# Roster Endpoints
# =============================================================================

@app.route('/api/roster', methods=['GET'])
def api_get_roster():
    """
    Load current roster from roster.json.
    
    Returns:
    {
        "success": true,
        "roster": {
            "captains": [...],
            "crew": [...],
            "ships": [...]
        }
    }
    """
    try:
        roster = _load_roster()
        if roster is None:
            # File doesn't exist or couldn't be loaded - return empty roster
            return jsonify({
                "success": True,
                "roster": Roster().to_dict()
            })
        
        return jsonify({
            "success": True,
            "roster": roster.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/roster', methods=['POST'])
def api_save_roster():
    """
    Save updated roster to roster.json.
    
    Expected JSON body:
    {
        "captains": [...],
        "crew": [...],
        "ships": [...]
    }
    
    Returns:
    {
        "success": true,
        "message": "Roster saved successfully"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body provided"}), 400

        roster = Roster.from_dict(data)
        success = _save_roster(roster)

        if success:
            return jsonify({
                "success": True,
                "message": "Roster saved successfully",
                "captain_count": len(roster.captains),
                "crew_count": len(roster.crew)
            })
        else:
            return jsonify({"success": False, "error": "Failed to save roster"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# Ship Config Endpoints
# =============================================================================

@app.route('/api/ship-config', methods=['GET'])
def api_get_ship_config():
    """
    Load current ship configuration from ship_config.json.
    
    Returns:
    {
        "success": true,
        "config": { ... }
    }
    """
    try:
        config = _load_ship_config()
        if config is None:
            return jsonify({"success": False, "error": "Could not load ship config file"}), 404
        
        return jsonify({
            "success": True,
            "config": config.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/ship-config', methods=['POST'])
def api_save_ship_config():
    """
    Save ship configuration to ship_config.json.
    
    Expected JSON body:
    {
        "ship_name": "My Ship",
        "captain": {...},
        "crew": [...],
        "equipment": {...},
        "active_building_bonuses": {...},
        "active_consumables": [...]
    }
    
    Returns:
    {
        "success": true,
        "message": "Ship configuration saved successfully"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body provided"}), 400

        config = ShipConfig.from_dict(data)
        success = _save_ship_config(config)

        if success:
            return jsonify({
                "success": True,
                "message": "Ship configuration saved successfully"
            })
        else:
            return jsonify({"success": False, "error": "Failed to save ship configuration"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# Utility Endpoints
# =============================================================================

@app.route('/api/crew-types', methods=['GET'])
def api_get_crew_types():
    """
    Get list of all valid crew types.
    
    Returns:
    {
        "success": true,
        "crew_types": ["Travelling Drunk", "Stowaway", ...]
    }
    """
    from models import CREW_TYPES
    return jsonify({
        "success": True,
        "crew_types": CREW_TYPES
    })


@app.route('/api/shipwrights', methods=['GET'])
def api_get_shipwright_types():
    """
    Get list of all valid shipwright building types with their bonuses.
    
    Returns:
    {
        "success": true,
        "shipwrights": [
            {"name": "Dilapidated Shipwright", "bonuses": {...}},
            ...
        ]
    }
    """
    from models import SHIPWRIGHT_TYPES
    shipwrights = []
    for stype in SHIPWRIGHT_TYPES:
        bonuses = get_shipwright_bonuses(stype)
        shipwrights.append({
            "name": stype,
            "bonuses": bonuses.to_dict()
        })
    return jsonify({
        "success": True,
        "shipwrights": shipwrights
    })


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """
    Get application configuration constants.
    
    Returns:
    {
        "success": true,
        "config": {
            "max_captains": 5,
            "max_crew": 25,
            "crew_types": [...],
            "shipwright_types": [...]
        }
    }
    """
    from models import MAX_CAPTAINS, MAX_CREW, CREW_TYPES, SHIPWRIGHT_TYPES
    return jsonify({
        "success": True,
        "config": {
            "max_captains": MAX_CAPTAINS,
            "max_crew": MAX_CREW,
            "crew_types": CREW_TYPES,
            "shipwright_types": SHIPWRIGHT_TYPES
        }
    })


@app.route('/api/health', methods=['GET'])
def api_health():
    """
    Health check endpoint.
    
    Returns:
    {
        "success": true,
        "status": "ok"
    }
    """
    return jsonify({"success": True, "status": "ok"})


# =============================================================================
# Main Entry Point
# =============================================================================

def run_server(host='127.0.0.1', port=5000, debug=False):
    """
    Run the Flask API server.
    
    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 5000)
        debug: Enable debug mode (default: False)
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
