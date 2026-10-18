"""Fixed acceptance tests: separate HTTP process and real SQLite per test."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class AppointmentE2E(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.server = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name('clinic.py')),
             str(Path(self.directory.name) / 'clinic.sqlite3')],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.addCleanup(self.stop_server)
        # The outer test/drill command has a finite timeout, including startup.
        self.port = int(self.server.stdout.readline())

    def stop_server(self):
        self.server.terminate()
        try:
            self.server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.server.kill()
            self.server.wait(timeout=3)
        self.server.stdout.close()
        self.server.stderr.close()

    def book(self, patient='Synthetic Patient', slot='2030-01-01T10:00:00Z'):
        request = Request(f'http://127.0.0.1:{self.port}/appointments',
                          data=json.dumps({'patient': patient, 'slot': slot}).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as response_error:
            response = response_error
        with response:
            return response.status, json.load(response)

    def test_create(self):
        status, body = self.book()
        self.assertEqual(status, 201)
        self.assertEqual(body['patient'], 'Synthetic Patient')

    def test_empty_patient_rejected(self):
        status, _ = self.book(patient='   ')
        self.assertEqual(status, 400)

    def test_duplicate_slot_rejected(self):
        self.assertEqual(self.book()[0], 201)
        self.assertEqual(self.book(patient='Another Synthetic Patient')[0], 409)


if __name__ == '__main__':
    unittest.main(verbosity=2)
