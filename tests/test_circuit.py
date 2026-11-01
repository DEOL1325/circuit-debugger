import copy
import unittest
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app


GOOD = {
    "positive": "E1", "negative": "E20",
    "components": [
        {"id": "R1", "kind": "resistor", "pins": ["B5", "B10"]},
        {"id": "D1", "kind": "led", "pins": ["D10", "D15"]},
        {"id": "W1", "kind": "wire", "pins": ["A1", "A5"]},
        {"id": "W2", "kind": "wire", "pins": ["A15", "A20"]},
    ],
}


class CircuitTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.circuit = copy.deepcopy(GOOD)

    def check(self):
        response = self.client.post('/api/check', json=self.circuit)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def codes(self):
        return [f['code'] for f in self.check()['findings']]

    def test_correct_circuit(self):
        self.assertEqual(self.check()['status'], 'topology_pass')

    def test_open_connection(self):
        self.circuit['components'][0]['pins'][1] = 'B11'
        self.assertEqual(self.codes(), ['open_connection'])

    def test_reversed_led(self):
        self.circuit['components'][1]['pins'].reverse()
        self.assertEqual(self.codes(), ['led_reversed'])

    def test_supply_short(self):
        self.circuit['components'].append({'id':'W3','kind':'wire','pins':['B1','B20']})
        self.assertIn('supply_short', self.codes())

    def test_bypassed_resistor(self):
        self.circuit['components'].append({'id':'W3','kind':'wire','pins':['A5','A10']})
        self.assertIn('component_bypassed', self.codes())

    def test_center_gap_is_not_connected(self):
        self.circuit['components'][1]['pins'][0] = 'G10'
        self.assertIn('open_connection', self.codes())

    def test_resistor_can_be_after_led(self):
        self.circuit['components'][0]['pins'] = ['B10','B15']
        self.circuit['components'][1]['pins'] = ['D5','D10']
        self.assertEqual(self.check()['status'], 'topology_pass')

    def test_resistor_orientation_does_not_matter(self):
        self.circuit['components'][0]['pins'].reverse()
        self.assertEqual(self.check()['status'], 'topology_pass')

    def test_equivalent_shifted_layout(self):
        self.circuit['positive'], self.circuit['negative'] = 'J2', 'J21'
        for c in self.circuit['components']:
            c['pins'] = [chr(ord(p[0])+5)+str(int(p[1:])+1) for p in c['pins']]
        self.assertEqual(self.check()['status'], 'topology_pass')

    def test_missing_component(self):
        self.circuit['components'].pop(1)
        self.assertIn('unsupported_parts', self.codes())

    def test_invalid_hole_rejected(self):
        self.circuit['positive'] = 'A31'
        self.assertEqual(self.client.post('/api/check', json=self.circuit).status_code, 422)

    def test_duplicate_ids_rejected(self):
        self.circuit['components'][1]['id'] = 'R1'
        self.assertEqual(self.client.post('/api/check', json=self.circuit).status_code, 422)

    def test_missing_model_does_not_fake_predictions(self):
        with patch('backend.app.MODEL_PATH', Path('/nonexistent/circuit-model.pt')):
            response = self.client.post('/api/detect', json={'image':'invalid'})
        self.assertEqual(response.status_code, 503)
        self.assertIn('No trained vision model', response.json()['detail'])


if __name__ == '__main__':
    unittest.main()
