"""Real legacy/enhanced HTTP projection and safe UI integration checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/q-cockpit'))
import q_cockpit_plus as cockpit
import test_local_dashboard as dashboard


class CockpitProvenanceTests(unittest.TestCase):
    def test_actual_renderer_displays_host_and_orchestrator_as_separate_text(self):
        # Execute the shipped renderer and translations, not a parallel formatter.
        # This text-only DOM harness is not a substitute for the parent's browser probe.
        ui = (ROOT / 'tools/q-cockpit/ui/index.html').read_text()
        translations = ui[ui.index('const I18N ='):ui.index("let currentLang =")]
        translate = ui[ui.index('function t('):ui.index("let currentTab =")]
        renderer = ui[ui.index('function renderCommunication('):ui.index('function updateSliceBudget(')]
        script = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  const fixture = JSON.parse(input);
  class Element {
    constructor() { this.children = []; this.text = ''; }
    set textContent(value) { this.text = String(value); this.children = []; }
    get textContent() { return this.text + this.children.map(child => child.textContent).join(''); }
    set innerHTML(value) { throw new Error('HTML sink used'); }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this.children = children; this.text = ''; }
  }
  const nodes = new Map();
  const document = {
    createElement: () => new Element(),
    getElementById: id => {
      if (!nodes.has(id)) nodes.set(id, new Element());
      return nodes.get(id);
    }
  };
  const context = vm.createContext({document});
  vm.runInContext(fixture.source, context);
  for (const [language, hostLabel, orchestratorLabel, unknown] of [
      ['en', 'host', 'orchestrator', 'unknown'],
      ['es', 'anfitrión', 'orquestador', 'desconocido']]) {
    vm.runInContext(`currentLang = '${language}'`, context);
    context.renderCommunication({events: [{provenance: {
      host: 'OpenCode', orchestrator: 'Gentle AI', lifecycle: 'loaded'
    }}]});
    let card = nodes.get('communication-events').children[0];
    assert(card.children.some(node => node.textContent === `${hostLabel}: OpenCode`));
    assert(card.children.some(node => node.textContent === `${orchestratorLabel}: Gentle AI`));
    context.renderCommunication({events: [{provenance: {}}]});
    card = nodes.get('communication-events').children[0];
    assert(card.children.some(node => node.textContent === `${hostLabel}: ${unknown}`));
    assert(card.children.some(node => node.textContent === `${orchestratorLabel}: ${unknown}`));
    const malicious = '<img onerror=alert(1)>';
    context.renderCommunication({events: [{provenance: {host: malicious, orchestrator: malicious}}]});
    card = nodes.get('communication-events').children[0];
    assert(card.children.some(node => node.textContent === `${hostLabel}: ${malicious}`));
    assert(card.children.some(node => node.textContent === `${orchestratorLabel}: ${malicious}`));
    assert.equal(nodes.get('communication-events').children.length, 1);
  }
});
'''
        result = subprocess.run(['node', '-e', script],
            input=json.dumps({'source': translations + "let currentLang = 'en';\n" + translate + renderer}),
            text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_proof_then_stale_proof_never_claims_current_verification(self):
        fixture = dashboard.LocalDashboardTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.cli('add', 'T1', 'Fixture task')
        fixture.cli('verify', 'T1', '--request-id', 'proof', '--', sys.executable, '-c', 'pass')
        current = fixture.get()['local_execution']['tasks'][0]
        self.assertEqual(current['communication']['provenance']['lifecycle'], 'verified')
        fixture.git('commit', '--allow-empty', '-qm', 'invalidate proof')
        stale = fixture.get()['local_execution']['tasks'][0]
        self.assertTrue(stale['evidence_stale'])
        self.assertEqual(stale['communication']['provenance']['lifecycle'], 'unknown')
        self.assertNotIn('command', stale)
        self.assertNotIn('log_path', stale)

    def test_both_http_paths_read_only_private_and_package_version(self):
        for base in (cockpit.legacy.CockpitHTTPHandler, cockpit.EnhancedHandler):
            with self.subTest(handler=base.__name__), tempfile.TemporaryDirectory(prefix='cockpit-provenance.') as temp:
                root = Path(temp)
                project = root / 'project'
                project.mkdir()
                (project / 'skill.json').write_text('{"version":"fixture-not-framework"}')
                manager = cockpit.EnhancedSessionManager(root / 'home')
                session = manager.create_session(project, 'Fixture')
                (session / 'events.jsonl').write_text(json.dumps({
                    'type': 'answer', 'timestamp': '2026-01-02T03:04:05+00:00',
                    'answer': 'PRIVATE', 'feedback': 'PRIVATE', 'notes': 'PRIVATE',
                    'argv': ['PRIVATE'], 'output': 'PRIVATE', 'log_path': '/PRIVATE',
                    'provenance': {'emitter': {'kind': 'tool', 'name': '<img onerror=alert(1)>'},
                                   'lifecycle': 'loaded'}}) + '\n')
                before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                handler = type('FixtureHandler', (base,), {
                    'project_root': project, 'session_manager': manager, 'active_session_dir': session})
                server = cockpit.legacy.ThreadedTCPServer(('127.0.0.1', 0), handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{server.server_address[1]}/api/communication') as response:
                        raw = response.read().decode()
                        data = json.loads(raw)
                    self.assertNotIn('PRIVATE', raw)
                    self.assertNotIn(str(root), raw)
                    self.assertEqual(data['framework_version'], json.loads((ROOT / 'skill.json').read_text())['version'])
                    self.assertEqual(data['events'][0]['provenance']['lifecycle'], 'loaded')
                    self.assertEqual(data['events'][0]['provenance']['emitter']['name'], '<img onerror=alert(1)>')
                    self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()})
                    # An escaped event file cannot disclose even allowlisted labels.
                    event_file = session / 'events.jsonl'
                    event_file.unlink()
                    event_file.symlink_to(project / 'skill.json')
                    with urllib.request.urlopen(f'http://127.0.0.1:{server.server_address[1]}/api/communication') as response:
                        rejected = json.load(response)
                    self.assertEqual(rejected['status'], 'unavailable')
                    self.assertEqual(rejected['events'], [])
                finally:
                    server.shutdown()
                    server.server_close()

    def test_ui_uses_safe_activity_dom_and_dynamic_footer(self):
        ui = (ROOT / 'tools/q-cockpit/ui/index.html').read_text()
        self.assertNotIn('q-cockpit v2.5.3', ui)
        self.assertIn('function renderCommunication(', ui)
        activity = ui.split('function renderCommunication(', 1)[1].split('function ', 1)[0]
        self.assertIn('textContent', activity)
        self.assertIn('replaceChildren', activity)
        self.assertNotIn('innerHTML', activity)
