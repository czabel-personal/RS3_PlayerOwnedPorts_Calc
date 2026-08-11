"""
Unit tests for the Flask API endpoints.

Tests all API routes defined in api.py:
- POST /api/optimize
- GET /api/roster
- POST /api/roster
- GET /api/ship-config
- POST /api/ship-config
- GET /api/crew-types
- GET /api/shipwrights
- GET /api/health
"""

import unittest
import json
import os
import tempfile
import copy

from flask import Flask
from models import (
    Roster, ShipConfig, VoyageTarget, BuildingBonuses,
    ConsumableBuff, Captain, CrewMember, Stats,
    ShipPart
)
from api import app, _load_roster, _save_roster, _load_ship_config, _save_ship_config


class TestHealthEndpoint(unittest.TestCase):
    """Test the health check endpoint."""

    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health_returns_ok(self):
        """Test that /api/health returns success."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'ok')


class TestCrewTypesEndpoint(unittest.TestCase):
    """Test the crew types endpoint."""

    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_crew_types_returns_list(self):
        """Test that /api/crew-types returns valid crew types."""
        response = self.client.get('/api/crew-types')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('crew_types', data)
        self.assertIsInstance(data['crew_types'], list)
        self.assertGreater(len(data['crew_types']), 0)
        self.assertIn('Travelling Drunk', data['crew_types'])


class TestShipwrightsEndpoint(unittest.TestCase):
    """Test the shipwrights endpoint."""

    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_shipwrights_returns_list(self):
        """Test that /api/shipwrights returns valid shipwright types."""
        response = self.client.get('/api/shipwrights')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('shipwrights', data)
        self.assertIsInstance(data['shipwrights'], list)
        self.assertGreater(len(data['shipwrights']), 0)
        # Check structure
        first = data['shipwrights'][0]
        self.assertIn('name', first)
        self.assertIn('bonuses', first)


class TestRosterEndpoints(unittest.TestCase):
    """Test roster GET and POST endpoints."""

    def setUp(self):
        """Set up test client and temporary roster file."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_roster_file = os.path.join(self.temp_dir, 'test_roster.json')

    def _create_sample_roster(self) -> Roster:
        """Create a sample roster for testing."""
        captain = Captain(
            name='Captain Stubbs',
            base_stats=Stats(morale=100, combat=100, seafaring=100),
            current_stats=Stats(morale=100, combat=100, seafaring=100),
            level=1,
            traits=['Leader']
        )
        crew_member = CrewMember(
            name='First Mate',
            base_stats=Stats(morale=50, combat=50, seafaring=50),
            current_stats=Stats(morale=50, combat=50, seafaring=50),
            level=1
        )
        return Roster(
            captains=[captain],
            crew=[crew_member],
            ships=[]
        )

    def test_get_roster_no_file(self):
        """Test GET /api/roster when no roster file exists."""
        # Ensure no file exists
        if os.path.exists(self.temp_roster_file):
            os.remove(self.temp_roster_file)
        
        # Temporarily override the ROSTER_FILE
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            response = self.client.get('/api/roster')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            # Should return empty roster
            self.assertEqual(len(data['roster']['captains']), 0)
            self.assertEqual(len(data['roster']['crew']), 0)
        finally:
            api.ROSTER_FILE = original

    def test_get_roster_with_file(self):
        """Test GET /api/roster when roster file exists."""
        roster = self._create_sample_roster()
        _save_roster(roster, self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            response = self.client.get('/api/roster')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(len(data['roster']['captains']), 1)
            self.assertEqual(len(data['roster']['crew']), 1)
            self.assertEqual(data['roster']['captains'][0]['name'], 'Captain Stubbs')
        finally:
            api.ROSTER_FILE = original

    def test_post_roster(self):
        """Test POST /api/roster saves roster correctly."""
        roster = self._create_sample_roster()
        roster_dict = roster.to_dict()
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            response = self.client.post(
                '/api/roster',
                data=json.dumps(roster_dict),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['captain_count'], 1)
            self.assertEqual(data['crew_count'], 1)
            
            # Verify file was saved
            loaded = _load_roster(self.temp_roster_file)
            self.assertEqual(len(loaded.captains), 1)
            self.assertEqual(loaded.captains[0].name, 'Captain Stubbs')
        finally:
            api.ROSTER_FILE = original

    def test_post_roster_invalid(self):
        """Test POST /api/roster with invalid data."""
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            response = self.client.post(
                '/api/roster',
                data='not json',
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)
        finally:
            api.ROSTER_FILE = original


class TestShipConfigEndpoints(unittest.TestCase):
    """Test ship config GET and POST endpoints."""

    def setUp(self):
        """Set up test client and temporary config file."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_file = os.path.join(self.temp_dir, 'test_ship_config.json')

    def _create_sample_config(self) -> ShipConfig:
        """Create a sample ship config for testing."""
        captain = Captain(
            name='Captain Stubbs',
            base_stats=Stats(morale=100, combat=100, seafaring=100),
            current_stats=Stats(morale=100, combat=100, seafaring=100),
            level=1
        )
        return ShipConfig(
            ship_name='Black Pearl',
            captain=captain,
            crew=[],
            active_building_bonuses=BuildingBonuses(morale=0.03, combat=0.03, seafaring=0.05)
        )

    def test_get_ship_config_no_file(self):
        """Test GET /api/ship-config when no config file exists."""
        if os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
        
        import api
        original = api.SHIP_CONFIG_FILE
        api.SHIP_CONFIG_FILE = self.temp_config_file
        
        try:
            response = self.client.get('/api/ship-config')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
        finally:
            api.SHIP_CONFIG_FILE = original

    def test_post_ship_config(self):
        """Test POST /api/ship-config saves config correctly."""
        config = self._create_sample_config()
        config_dict = config.to_dict()
        
        import api
        original = api.SHIP_CONFIG_FILE
        api.SHIP_CONFIG_FILE = self.temp_config_file
        
        try:
            response = self.client.post(
                '/api/ship-config',
                data=json.dumps(config_dict),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify file was saved
            loaded = _load_ship_config(self.temp_config_file)
            self.assertEqual(loaded.ship_name, 'Black Pearl')
        finally:
            api.SHIP_CONFIG_FILE = original


class TestOptimizeEndpoint(unittest.TestCase):
    """Test the optimization endpoint."""

    def setUp(self):
        """Set up test client and temporary roster file."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_roster_file = os.path.join(self.temp_dir, 'test_roster.json')

    def _create_sample_roster(self) -> Roster:
        """Create a sample roster for testing."""
        captains = [
            Captain(
                name='Captain Stubbs',
                base_stats=Stats(morale=100, combat=100, seafaring=100),
                current_stats=Stats(morale=100, combat=100, seafaring=100),
                level=1,
                traits=['Leader']
            ),
            Captain(
                name='Captain Brineyare',
                base_stats=Stats(morale=80, combat=120, seafaring=90),
                current_stats=Stats(morale=80, combat=120, seafaring=90),
                level=1,
                traits=['Tactician']
            )
        ]
        crew = [
            CrewMember(
                name='First Mate',
                base_stats=Stats(morale=50, combat=50, seafaring=50),
                current_stats=Stats(morale=50, combat=50, seafaring=50),
                level=1
            ),
            CrewMember(
                name='Navigator',
                base_stats=Stats(morale=30, combat=30, seafaring=80),
                current_stats=Stats(morale=30, combat=30, seafaring=80),
                level=1
            ),
            CrewMember(
                name='Gunner',
                base_stats=Stats(morale=20, combat=80, seafaring=20),
                current_stats=Stats(morale=20, combat=80, seafaring=20),
                level=1
            )
        ]
        return Roster(captains=captains, crew=crew, ships=[])

    def test_optimize_with_valid_data(self):
        """Test POST /api/optimize with valid data."""
        roster = self._create_sample_roster()
        _save_roster(roster, self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            request_data = {
                'voyage_target': {
                    'morale': 100,
                    'combat': 150,
                    'seafaring': 120
                },
                'building_bonuses': {
                    'morale': 0.03,
                    'combat': 0.03,
                    'seafaring': 0.05
                },
                'consumables': [],
                'max_results': 5
            }
            
            response = self.client.post(
                '/api/optimize',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('results', data)
            self.assertIn('total_combinations', data)
            self.assertIsInstance(data['results'], list)
            self.assertGreater(len(data['results']), 0)
            
            # Check result structure
            first_result = data['results'][0]
            self.assertIn('assignment', first_result)
            self.assertIn('composite_score', first_result)
            self.assertIn('meets_targets', first_result)
            self.assertIn('captain_name', first_result['assignment'])
            self.assertIn('crew_members', first_result['assignment'])
            self.assertIn('final_stats', first_result['assignment'])
        finally:
            api.ROSTER_FILE = original

    def test_optimize_with_shipwright_type(self):
        """Test POST /api/optimize using shipwright_type."""
        roster = self._create_sample_roster()
        _save_roster(roster, self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            request_data = {
                'voyage_target': {
                    'morale': 100,
                    'combat': 150,
                    'seafaring': 120
                },
                'shipwright_type': 'Maritime Shipwright',
                'consumables': [],
                'max_results': 5
            }
            
            response = self.client.post(
                '/api/optimize',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
        finally:
            api.ROSTER_FILE = original

    def test_optimize_no_roster(self):
        """Test POST /api/optimize when no roster file exists."""
        if os.path.exists(self.temp_roster_file):
            os.remove(self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            request_data = {
                'voyage_target': {'morale': 100, 'combat': 150, 'seafaring': 120},
                'building_bonuses': {'morale': 0.03, 'combat': 0.03, 'seafaring': 0.05},
                'consumables': []
            }
            
            response = self.client.post(
                '/api/optimize',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            # Returns 404 because roster file doesn't exist
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
        finally:
            api.ROSTER_FILE = original

    def test_optimize_no_json_body(self):
        """Test POST /api/optimize with no JSON body."""
        roster = self._create_sample_roster()
        _save_roster(roster, self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            response = self.client.post(
                '/api/optimize',
                data='not json',
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)
        finally:
            api.ROSTER_FILE = original

    def test_optimize_result_ranking(self):
        """Test that results are ranked by composite score descending."""
        roster = self._create_sample_roster()
        _save_roster(roster, self.temp_roster_file)
        
        import api
        original = api.ROSTER_FILE
        api.ROSTER_FILE = self.temp_roster_file
        
        try:
            request_data = {
                'voyage_target': {
                    'morale': 50,
                    'combat': 50,
                    'seafaring': 50
                },
                'building_bonuses': {'morale': 0, 'combat': 0, 'seafaring': 0},
                'consumables': [],
                'max_results': 10
            }
            
            response = self.client.post(
                '/api/optimize',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Check that scores are in descending order
            scores = [r['composite_score'] for r in data['results']]
            self.assertEqual(scores, sorted(scores, reverse=True))
        finally:
            api.ROSTER_FILE = original


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions for file I/O."""

    def setUp(self):
        """Set up temporary directory."""
        self.temp_dir = tempfile.mkdtemp()

    def test_save_and_load_roster(self):
        """Test _save_roster and _load_roster helper functions."""
        roster = Roster(
            captains=[Captain('Test Captain', Stats(100, 100, 100), level=1)],
            crew=[CrewMember('Test Crew', Stats(50, 50, 50), level=1)],
            ships=[]
        )
        filepath = os.path.join(self.temp_dir, 'test.json')
        
        self.assertTrue(_save_roster(roster, filepath))
        loaded = _load_roster(filepath)
        self.assertEqual(len(loaded.captains), 1)
        self.assertEqual(loaded.captains[0].name, 'Test Captain')

    def test_save_and_load_ship_config(self):
        """Test _save_ship_config and _load_ship_config helper functions."""
        config = ShipConfig(
            ship_name='Test Ship',
            captain=Captain('Test Captain', Stats(100, 100, 100), level=1),
            active_building_bonuses=BuildingBonuses(morale=0.05, combat=0.05, seafaring=0.05)
        )
        filepath = os.path.join(self.temp_dir, 'test.json')
        
        self.assertTrue(_save_ship_config(config, filepath))
        loaded = _load_ship_config(filepath)
        self.assertEqual(loaded.ship_name, 'Test Ship')

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file returns None."""
        filepath = os.path.join(self.temp_dir, 'nonexistent.json')
        
        roster = _load_roster(filepath)
        self.assertIsNone(roster)
        
        config = _load_ship_config(filepath)
        # Ship config returns empty config (not None) for missing files
        self.assertIsInstance(config, ShipConfig)


if __name__ == '__main__':
    unittest.main()
