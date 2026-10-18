"""Deliberately defective HTTP fixture for hosted repair drills. Never deploy."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3


class Clinic(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            patient = data.get('patient', '').strip()
            slot = data['slot']
            if not isinstance(slot, str) or not slot:
                raise ValueError('slot required')
            # Deliberate defect: empty patient names are accepted.
            self.server.db.execute('INSERT INTO appointments VALUES (?, ?)', (slot, patient))
            self.server.db.commit()
            status, payload = 201, {'patient': patient, 'slot': slot}
        except (ValueError, KeyError, TypeError, AttributeError):
            status, payload = 400, {'error': 'invalid appointment'}
        except sqlite3.IntegrityError:
            self.server.db.rollback()
            status, payload = 409, {'error': 'slot already booked'}
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


def serve(database, address=('127.0.0.1', 0)):
    server = HTTPServer(address, Clinic)
    server.db = sqlite3.connect(database)
    server.db.execute('PRAGMA journal_mode=WAL')
    server.db.execute('PRAGMA busy_timeout=5000')
    # Deliberate defect: slot uniqueness is missing.
    server.db.execute('CREATE TABLE appointments (slot TEXT, patient TEXT NOT NULL)')
    print(server.server_address[1], flush=True)
    try:
        server.serve_forever()
    finally:
        server.db.close()
        server.server_close()


if __name__ == '__main__':
    import sys
    serve(sys.argv[1])
