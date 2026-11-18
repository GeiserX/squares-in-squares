#!/usr/bin/env python3
"""Regression checks for numeric register witnesses."""
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harvest_register as H


class WitnessScalars(unittest.TestCase):
    def test_field_order_and_tiny_root_bracket(self):
        scale = 10 ** 120
        lower = math.isqrt(2 * scale * scale)
        reader = H.scalar_reader(dict(kind='algebraic-number-field',
            minimal_polynomial=['1', '0', '-2'],
            isolating_interval=[f'{lower}/{scale}', f'{lower+1}/{scale}']))
        self.assertAlmostEqual(float(reader(['3', '2'])), 3 + 2 * math.sqrt(2), places=14)

    def test_unbracketed_field_and_wide_enclosure_fail(self):
        with self.assertRaises(ValueError):
            H.scalar_reader(dict(kind='algebraic-number-field',
                minimal_polynomial=['1', '0', '-2'], isolating_interval=['2', '3']))
        reader = H.scalar_reader(dict(kind='interval-enclosure'))
        for pair in (['0', '1'], ['1', '0']):
            with self.assertRaises(ValueError):
                reader(pair)
        self.assertAlmostEqual(float(reader(['0.5', '0.50000000000001'])), .5, places=12)

    def test_rotated_field_witness_and_nonunit_basis(self):
        import yaml
        witness = dict(n=1, square_size='1', representation='center-basis',
            scalar=dict(kind='algebraic-number-field', minimal_polynomial=['1', '0', '-2'], isolating_interval=['1', '2']),
            squares=[dict(center=[['0', '1/2'], ['0', '1/2']], basis=[['0', '1/2'], ['0', '1/2']])])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'w.yaml'
            path.write_text(yaml.safe_dump(dict(witness=witness)))
            n, squares = H.read_witness(path)
            self.assertEqual(n, 1)
            self.assertAlmostEqual(H.side(squares), math.sqrt(2), places=14)
            self.assertAlmostEqual(float(squares[0][2]), math.pi / 4, places=14)
            witness['squares'][0]['basis'] = ['1', '1']
            path.write_text(yaml.safe_dump(dict(witness=witness)))
            with self.assertRaises(ValueError):
                H.read_witness(path)
            path.write_text('schema: Witness/v2\n')
            self.assertIsNone(H.read_witness(path))


if __name__ == '__main__':
    unittest.main()
