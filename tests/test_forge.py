import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from orchestra_forge.cli import main
from orchestra_forge.composition import load_composition
from orchestra_forge.midi import write_midi

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/demo.json'

class ForgeTests(unittest.TestCase):
    def test_duration_and_tracks(self):
        composition = load_composition(EXAMPLE)
        self.assertEqual(composition.seconds, 6)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'demo.mid'
            write_midi(path, composition)
            blob = path.read_bytes()
            self.assertEqual(struct.unpack('>4sIHHH', blob[:14]), (b'MThd', 6, 1, 3, 480))
            self.assertEqual(blob.count(b'MTrk'), 3)

    def test_demo_writes_midi_to_midi_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            midi, wav = Path(tmp)/'new.mid', Path(tmp)/'new.wav'
            with patch('orchestra_forge.cli._render') as render:
                self.assertEqual(main(['demo', '--composition', str(EXAMPLE), '--midi', str(midi), '--output', str(wav)]), 0)
                render.assert_called_once_with(midi, None, wav)
            self.assertTrue(midi.read_bytes().startswith(b'MThd'))
            self.assertFalse(wav.exists())

    def test_invalid_notes(self):
        data = json.loads(EXAMPLE.read_text())
        for note in ([0,1,128,50], [-1,1,60,50], [7,2,60,50], [0,1,60,0], [0,1,60.5,50]):
            with self.subTest(note=note), tempfile.TemporaryDirectory() as tmp:
                data['parts'][0]['notes'] = [note]
                path = Path(tmp)/'bad.json'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError): load_composition(path)

    def test_duplicate_channels(self):
        data = json.loads(EXAMPLE.read_text())
        data['parts'][1]['channel'] = 0
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.json'; path.write_text(json.dumps(data))
            with self.assertRaises(ValueError): load_composition(path)

    def test_no_overwrite_input(self):
        self.assertEqual(main(['compose', '--composition', str(EXAMPLE), '--output', str(EXAMPLE)]), 1)

    def test_missing_input(self):
        self.assertEqual(main(['compose', '--composition', '/nonexistent/forge.json', '--output', '/tmp/unused.mid']), 1)

    def test_unicode_long_track_name(self):
        data = json.loads(EXAMPLE.read_text()); data['parts'][0]['name'] = '弦' * 100
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'unicode.json'; path.write_text(json.dumps(data))
            write_midi(Path(tmp)/'unicode.mid', load_composition(path))

class AudiolizerAndMeterTests(unittest.TestCase):
    def test_catalogue_and_validation(self):
        from orchestra_forge.audiolizer import NAMES, number
        self.assertEqual(len(NAMES), 128)
        self.assertEqual(NAMES[4], 'Electric Piano 1')
        self.assertEqual(number({'pitch':60}, 'pitch', 24, 96, True), 60)
        with self.assertRaises(ValueError): number({'pitch':True}, 'pitch', 24, 96, True)

    def test_six_eight_metadata(self):
        data = json.loads(EXAMPLE.read_text()); data['time_signature'] = [6,8]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'meter.json'; path.write_text(json.dumps(data))
            score = load_composition(path)
            midi = Path(tmp)/'meter.mid'; write_midi(midi,score)
            self.assertEqual(score.time_signature, (6,8))
            self.assertIn(bytes.fromhex('ff580406032408'), midi.read_bytes())

if __name__ == '__main__': unittest.main()
