#!/usr/bin/env node
/**
 * audit_api_contracts.js - Deterministic Technical Contracts Audit Gate
 * Validates 4 core technical contracts with zero external dependencies:
 *   1. GitHub & CI Integrity (A03)
 *   2. Disaster Recovery Contract (A17)
 *   3. Observability & Telemetry (A14)
 *   4. API Contracts Catalog (A06)
 *
 * Supported CLI flags:
 *   --cwd <path>  Target directory to audit (default: ".")
 *   --strict      Treat warnings as errors (exit code 1 if any warning)
 *   --json        Output result as structured JSON
 *   --help        Display usage instructions
 */

const fs = require('fs');
const path = require('path');
const process = require('process');

const BASE_IGNORED_DIRS = new Set([
  '.git',
  'node_modules',
  '__pycache__',
  '.venv',
  'venv',
  'env',
  '.env',
  'dist',
  'build',
  '.idea',
  '.vscode',
  'coverage',
  '.cache',
  '.turbo',
  '.next',
  '.nuxt'
]);

const DOC_IGNORED_DIRS = new Set([
  ...BASE_IGNORED_DIRS,
  'references',
  'docs',
  'prompts',
  'templates',
  'odd',
  'audit',
  'tests',
  'test'
]);

/**
 * Recursively find files matching filter up to maxDepth.
 */
function findFiles(baseDir, filterFn, maxDepth = 4, ignoredDirs = BASE_IGNORED_DIRS, currentDepth = 0) {
  if (currentDepth > maxDepth || !fs.existsSync(baseDir)) {
    return [];
  }
  const results = [];
  try {
    const entries = fs.readdirSync(baseDir, { withFileTypes: true });
    for (const entry of entries) {
      if (ignoredDirs.has(entry.name)) {
        continue;
      }
      const fullPath = path.join(baseDir, entry.name);
      if (entry.isDirectory()) {
        results.push(...findFiles(fullPath, filterFn, maxDepth, ignoredDirs, currentDepth + 1));
      } else if (entry.isFile()) {
        if (!filterFn || filterFn(entry.name, fullPath)) {
          results.push(fullPath);
        }
      }
    }
  } catch (_err) {
    // Ignore unreadable directories
  }
  return results;
}

/**
 * Safely read file content with a size cap (128 KB) to prevent performance hits.
 */
function safeRead(filePath, maxBytes = 131072) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buffer = Buffer.alloc(maxBytes);
    const bytesRead = fs.readSync(fd, buffer, 0, maxBytes, 0);
    fs.closeSync(fd);
    return buffer.toString('utf8', 0, bytesRead);
  } catch (_err) {
    return '';
  }
}

/**
 * Run deterministic audit on target directory.
 */
function auditTechnicalContracts(cwd) {
  const targetDir = path.resolve(cwd);
  const selfPath = path.resolve(__filename);

  const report = {
    target: targetDir,
    timestamp: new Date().toISOString(),
    contracts: {
      A03_github_ci_integrity: {
        id: 'A03',
        name: 'GitHub & CI Integrity',
        checks: []
      },
      A17_disaster_recovery: {
        id: 'A17',
        name: 'Disaster Recovery Contract',
        checks: []
      },
      A14_observability_telemetry: {
        id: 'A14',
        name: 'Observability & Telemetry',
        checks: []
      },
      A06_api_contracts: {
        id: 'A06',
        name: 'API Contracts Catalog',
        checks: []
      }
    },
    summary: {
      total: 0,
      passed: 0,
      warnings: 0,
      critical: 0,
      verdict: 'PASSED'
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // Source & Application Code Files
  // ──────────────────────────────────────────────────────────────────────────
  const auditScriptNames = new Set(['audit_api_contracts.js', 'validate_audit.py']);
  const codeFiles = findFiles(
    targetDir,
    (name, fullPath) => {
      if (auditScriptNames.has(name) || path.resolve(fullPath) === selfPath) return false;
      return /\.(py|js|ts|jsx|tsx|go|rs|php|rb|java|cs)$/i.test(name);
    },
    5,
    DOC_IGNORED_DIRS
  );

  // ──────────────────────────────────────────────────────────────────────────
  // CONTRACT A03: GitHub & CI Integrity
  // ──────────────────────────────────────────────────────────────────────────
  const a03 = report.contracts.A03_github_ci_integrity;

  // 1. .gitignore check
  const gitignorePath = path.join(targetDir, '.gitignore');
  if (fs.existsSync(gitignorePath)) {
    a03.checks.push({
      id: 'A03-GITIGNORE',
      name: 'VCS Ignore (.gitignore)',
      status: 'PASS',
      severity: 'PASS',
      message: '.gitignore exists at project root'
    });
  } else {
    a03.checks.push({
      id: 'A03-GITIGNORE',
      name: 'VCS Ignore (.gitignore)',
      status: 'FAIL',
      severity: 'CRITICAL',
      message: '.gitignore is missing at project root'
    });
  }

  // 2. CI workflows (.github/workflows/*.yml | *.yaml)
  const workflowsDir = path.join(targetDir, '.github', 'workflows');
  let workflowFiles = [];
  if (fs.existsSync(workflowsDir) && fs.statSync(workflowsDir).isDirectory()) {
    try {
      workflowFiles = fs.readdirSync(workflowsDir)
        .filter(f => f.endsWith('.yml') || f.endsWith('.yaml'))
        .map(f => path.join(workflowsDir, f));
    } catch (_err) {
      workflowFiles = [];
    }
  }

  if (workflowFiles.length > 0) {
    const relNames = workflowFiles.map(f => path.relative(targetDir, f)).join(', ');
    a03.checks.push({
      id: 'A03-WORKFLOWS',
      name: 'CI Workflow Definitions',
      status: 'PASS',
      severity: 'PASS',
      message: `Found ${workflowFiles.length} CI workflow file(s): ${relNames}`
    });
  } else {
    a03.checks.push({
      id: 'A03-WORKFLOWS',
      name: 'CI Workflow Definitions',
      status: 'FAIL',
      severity: 'CRITICAL',
      message: 'No CI workflow definitions (.yml/.yaml) found in .github/workflows/'
    });
  }

  // 3. Workflow triggers (push, pull_request)
  if (workflowFiles.length > 0) {
    const triggersFound = new Set();
    for (const wf of workflowFiles) {
      const content = safeRead(wf);
      if (/(?:^|\n)\s*(?:pull_request|pull_request_target)\s*:/m.test(content) ||
          /on:\s*\[?[^\]\n]*pull_request[^\]\n]*\]?/m.test(content)) {
        triggersFound.add('pull_request');
      }
      if (/(?:^|\n)\s*push\s*:/m.test(content) ||
          /on:\s*\[?[^\]\n]*push[^\]\n]*\]?/m.test(content)) {
        triggersFound.add('push');
      }
    }

    if (triggersFound.size > 0) {
      a03.checks.push({
        id: 'A03-TRIGGERS',
        name: 'Workflow Triggers',
        status: 'PASS',
        severity: 'PASS',
        message: `CI triggers verified (${Array.from(triggersFound).join(', ')})`
      });
    } else {
      a03.checks.push({
        id: 'A03-TRIGGERS',
        name: 'Workflow Triggers',
        status: 'WARN',
        severity: 'WARNING',
        message: 'No push or pull_request triggers found in workflow definitions'
      });
    }

    // 4. Test / Lint job steps
    let hasTestLint = false;
    const testPattern = /\b(test|lint|py_compile|unittest|pytest|eslint|jest|vitest|npm\s+(?:run\s+)?test|cargo\s+test|go\s+test|mvn\s+test|flake8|mypy|ruff)\b/i;
    for (const wf of workflowFiles) {
      const content = safeRead(wf);
      if (testPattern.test(content)) {
        hasTestLint = true;
        break;
      }
    }

    if (hasTestLint) {
      a03.checks.push({
        id: 'A03-TEST-LINT',
        name: 'Automated Test/Lint Gates',
        status: 'PASS',
        severity: 'PASS',
        message: 'Automated test and/or lint steps detected in CI workflows'
      });
    } else {
      a03.checks.push({
        id: 'A03-TEST-LINT',
        name: 'Automated Test/Lint Gates',
        status: 'WARN',
        severity: 'WARNING',
        message: 'No automated test or lint steps identified in CI workflows'
      });
    }
  } else {
    a03.checks.push({
      id: 'A03-TRIGGERS',
      name: 'Workflow Triggers',
      status: 'WARN',
      severity: 'WARNING',
      message: 'Cannot evaluate triggers: no workflow files found'
    });
    a03.checks.push({
      id: 'A03-TEST-LINT',
      name: 'Automated Test/Lint Gates',
      status: 'WARN',
      severity: 'WARNING',
      message: 'Cannot evaluate test/lint steps: no workflow files found'
    });
  }

  // 5. Dependabot / Renovate
  const dependabotYml = path.join(targetDir, '.github', 'dependabot.yml');
  const dependabotYaml = path.join(targetDir, '.github', 'dependabot.yaml');
  const renovateFiles = [
    'renovate.json',
    '.renovaterc',
    '.renovaterc.json',
    path.join('.github', 'renovate.json')
  ].map(f => path.join(targetDir, f));

  let depAutomationPath = null;
  if (fs.existsSync(dependabotYml)) depAutomationPath = '.github/dependabot.yml';
  else if (fs.existsSync(dependabotYaml)) depAutomationPath = '.github/dependabot.yaml';
  else {
    const foundRenovate = renovateFiles.find(p => fs.existsSync(p));
    if (foundRenovate) depAutomationPath = path.relative(targetDir, foundRenovate);
  }

  if (depAutomationPath) {
    a03.checks.push({
      id: 'A03-DEPENDABOT',
      name: 'Dependency Automation',
      status: 'PASS',
      severity: 'PASS',
      message: `Dependency automation configured (${depAutomationPath})`
    });
  } else {
    a03.checks.push({
      id: 'A03-DEPENDABOT',
      name: 'Dependency Automation',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No Dependabot (.github/dependabot.yml) or Renovate configuration found'
    });
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CONTRACT A17: Disaster Recovery Contract
  // ──────────────────────────────────────────────────────────────────────────
  const a17 = report.contracts.A17_disaster_recovery;

  // 1. Backup scripts/runbooks/configs
  const backupRegex = /(?:backup|snapshot|pg_dump|mysqldump|\bdr\b|disaster-recovery|mongodump)/i;
  const backupFiles = findFiles(
    targetDir,
    (name, fullPath) => {
      if (path.resolve(fullPath) === selfPath) return false;
      if (backupRegex.test(name)) return true;
      const rel = path.relative(targetDir, fullPath).toLowerCase();
      return (rel.startsWith('docs') || rel.startsWith('runbooks') || rel.startsWith('scripts')) && backupRegex.test(rel);
    },
    4,
    BASE_IGNORED_DIRS
  );

  let backupInWorkflows = false;
  for (const wf of workflowFiles) {
    const content = safeRead(wf);
    if (backupRegex.test(content)) {
      backupInWorkflows = true;
      break;
    }
  }

  if (backupFiles.length > 0 || backupInWorkflows) {
    const sample = backupFiles.map(f => path.relative(targetDir, f)).slice(0, 3);
    const detail = backupFiles.length > 0 ? sample.join(', ') : 'CI workflow steps';
    a17.checks.push({
      id: 'A17-BACKUP',
      name: 'Backup Strategy & Runbooks',
      status: 'PASS',
      severity: 'PASS',
      message: `Disaster recovery / backup artifacts detected: ${detail}`
    });
  } else {
    a17.checks.push({
      id: 'A17-BACKUP',
      name: 'Backup Strategy & Runbooks',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No backup scripts, snapshot configs, or DR runbooks found'
    });
  }

  // 2. Rollback capabilities in deploy workflows/scripts
  const rollbackRegex = /\b(rollback|canary|revert|blue-green|helm\s+rollback)\b/i;
  let rollbackFound = false;
  let rollbackLocation = '';

  const deployCandidates = findFiles(
    targetDir,
    (name, fullPath) => {
      if (path.resolve(fullPath) === selfPath) return false;
      const lower = name.toLowerCase();
      const rel = path.relative(targetDir, fullPath).toLowerCase();
      return (lower.includes('deploy') || rel.includes('k8s') || rel.includes('helm') ||
              rel.includes('terraform') || lower.endsWith('.sh') || lower.endsWith('.ps1')) &&
             !rel.startsWith('prompts') && !rel.startsWith('references');
    },
    4,
    DOC_IGNORED_DIRS
  );

  for (const f of [...workflowFiles, ...deployCandidates]) {
    const content = safeRead(f);
    if (rollbackRegex.test(content)) {
      rollbackFound = true;
      rollbackLocation = path.relative(targetDir, f);
      break;
    }
  }

  if (rollbackFound) {
    a17.checks.push({
      id: 'A17-ROLLBACK',
      name: 'Rollback & Resilience Capabilities',
      status: 'PASS',
      severity: 'PASS',
      message: `Rollback or canary deployment mechanisms identified (${rollbackLocation})`
    });
  } else {
    a17.checks.push({
      id: 'A17-ROLLBACK',
      name: 'Rollback & Resilience Capabilities',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No rollback, canary, or revert mechanisms identified in deploy workflows/scripts'
    });
  }

  // 3. Healthcheck definition
  let healthcheckFound = false;
  let healthcheckLocation = '';
  const healthPatterns = [
    /(?:^|\n)\s*HEALTHCHECK\b/m,
    /(?:^|\n)\s*healthcheck\s*:/m,
    /\b(readinessProbe|livenessProbe)\s*:/m,
    /["']\/(?:health|healthz|ping|livez|readyz)["']/i,
    /path\s*==\s*["']\/(?:health|healthz|ping)["']/i
  ];

  const serverCandidates = findFiles(
    targetDir,
    (name, fullPath) => {
      if (path.resolve(fullPath) === selfPath) return false;
      const lower = name.toLowerCase();
      return lower.includes('docker') || /\.(py|js|ts|go|yml|yaml)$/i.test(name);
    },
    4,
    DOC_IGNORED_DIRS
  );

  for (const f of serverCandidates) {
    const content = safeRead(f);
    for (const pat of healthPatterns) {
      if (pat.test(content)) {
        healthcheckFound = true;
        healthcheckLocation = path.relative(targetDir, f);
        break;
      }
    }
    if (healthcheckFound) break;
  }

  if (healthcheckFound) {
    a17.checks.push({
      id: 'A17-HEALTHCHECK',
      name: 'Healthcheck Endpoint',
      status: 'PASS',
      severity: 'PASS',
      message: `Healthcheck definition detected (${healthcheckLocation})`
    });
  } else {
    a17.checks.push({
      id: 'A17-HEALTHCHECK',
      name: 'Healthcheck Endpoint',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No healthcheck definition (/health, /healthz, /ping, or Docker HEALTHCHECK) found'
    });
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CONTRACT A14: Observability & Telemetry
  // ──────────────────────────────────────────────────────────────────────────
  const a14 = report.contracts.A14_observability_telemetry;

  // 1. Structured logging / APM / metrics
  const loggingKeywords = [
    'winston', 'pino', 'loguru', 'logging', 'sentry', 'opentelemetry',
    'prometheus', 'datadog', 'bunyan', 'morgan', 'serilog', 'structlog',
    'newrelic', 'dynatrace', 'statsd'
  ];
  const loggingRegex = new RegExp(`\\b(${loggingKeywords.join('|')})\\b`, 'i');

  const manifestFiles = [
    'package.json',
    'requirements.txt',
    'pyproject.toml',
    'Pipfile',
    'go.mod',
    'Cargo.toml',
    'composer.json'
  ].map(f => path.join(targetDir, f)).filter(p => fs.existsSync(p));

  let loggingFound = false;
  let detectedLogger = '';

  for (const mf of manifestFiles) {
    const content = safeRead(mf);
    const match = content.match(loggingRegex);
    if (match) {
      loggingFound = true;
      detectedLogger = `${match[1]} in ${path.relative(targetDir, mf)}`;
      break;
    }
  }

  if (!loggingFound) {
    for (const f of codeFiles) {
      const content = safeRead(f);
      if (/(?:import\s+logging\b|from\s+logging\s+import|require\(["'](?:pino|winston|bunyan)["']\)|from\s+loguru\s+import|import\s+loguru|@opentelemetry|datadog|prometheus_client)/i.test(content)) {
        loggingFound = true;
        detectedLogger = path.relative(targetDir, f);
        break;
      }
    }
  }

  if (loggingFound) {
    a14.checks.push({
      id: 'A14-LOGGING',
      name: 'Structured Logging / APM',
      status: 'PASS',
      severity: 'PASS',
      message: `Structured logging / APM / metrics configured (${detectedLogger})`
    });
  } else {
    a14.checks.push({
      id: 'A14-LOGGING',
      name: 'Structured Logging / APM',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No structured logging (pino/winston/loguru), APM, or metrics libraries detected'
    });
  }

  // 2. Request correlation / tracing middleware
  const correlationRegex = /\b(correlationId|correlation_id|requestId|request_id|x-request-id|traceparent|tracing|tracer|trace_id|distributed-tracing|X-Correlation-ID)\b/i;
  let correlationFound = false;
  let correlationLocation = '';

  for (const f of codeFiles) {
    const content = safeRead(f);
    if (correlationRegex.test(content)) {
      correlationFound = true;
      correlationLocation = path.relative(targetDir, f);
      break;
    }
  }

  if (correlationFound) {
    a14.checks.push({
      id: 'A14-TRACING',
      name: 'Request Correlation & Tracing',
      status: 'PASS',
      severity: 'PASS',
      message: `Request correlation or tracing detected (${correlationLocation})`
    });
  } else {
    a14.checks.push({
      id: 'A14-TRACING',
      name: 'Request Correlation & Tracing',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No request correlation (x-request-id / correlation_id) or tracing middleware detected'
    });
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CONTRACT A06: API Contracts Catalog
  // ──────────────────────────────────────────────────────────────────────────
  const a06 = report.contracts.A06_api_contracts;

  // 1. OpenAPI / Swagger specifications
  const specFiles = findFiles(
    targetDir,
    (name, fullPath) => {
      if (path.resolve(fullPath) === selfPath) return false;
      const lower = name.toLowerCase();
      return lower.startsWith('openapi.') || lower.startsWith('swagger.') ||
             lower === 'openapi.json' || lower === 'openapi.yaml' || lower === 'openapi.yml' ||
             lower === 'swagger.json' || lower === 'swagger.yaml' || lower === 'swagger.yml';
    },
    4,
    BASE_IGNORED_DIRS
  );

  if (specFiles.length > 0) {
    const relSpecs = specFiles.map(f => path.relative(targetDir, f)).join(', ');
    a06.checks.push({
      id: 'A06-OPENAPI',
      name: 'OpenAPI / Swagger Specs',
      status: 'PASS',
      severity: 'PASS',
      message: `OpenAPI/Swagger specification found: ${relSpecs}`
    });
  } else {
    a06.checks.push({
      id: 'A06-OPENAPI',
      name: 'OpenAPI / Swagger Specs',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No OpenAPI or Swagger specification files found (openapi.*, swagger.*)'
    });
  }

  // 2. Route definitions / Controller catalog
  let routesFound = false;
  let routesLocation = '';

  const routeDirNames = new Set(['routes', 'controllers', 'api', 'endpoints']);
  const routeDirs = [];
  try {
    const topEntries = fs.readdirSync(targetDir, { withFileTypes: true });
    for (const ent of topEntries) {
      if (ent.isDirectory() && routeDirNames.has(ent.name.toLowerCase())) {
        routeDirs.push(ent.name);
      }
    }
  } catch (_e) {}

  if (routeDirs.length > 0) {
    routesFound = true;
    routesLocation = `Directory ${routeDirs.join(', ')}`;
  } else {
    const routeFileNames = new Set([
      'routes.py', 'router.py', 'urls.py', 'api.py',
      'routes.js', 'routes.ts', 'router.js', 'router.ts'
    ]);
    const routeFiles = findFiles(
      targetDir,
      name => routeFileNames.has(name.toLowerCase()),
      4,
      DOC_IGNORED_DIRS
    );
    if (routeFiles.length > 0) {
      routesFound = true;
      routesLocation = path.relative(targetDir, routeFiles[0]);
    } else {
      // Check code content for route declarations
      const routeCodeRegex = /(?:@app\.(?:route|get|post|put|delete|patch)|@router\.(?:get|post|put|delete|patch)|app\.(?:get|post|put|delete|patch)\s*\(|router\.(?:get|post|put|delete|patch)\s*\(|path\s*==\s*["']\/api\/|["']\/api\/[a-zA-Z0-9_\-\/]+["'])/;
      for (const f of codeFiles) {
        const content = safeRead(f);
        if (routeCodeRegex.test(content)) {
          routesFound = true;
          routesLocation = path.relative(targetDir, f);
          break;
        }
      }
    }
  }

  if (routesFound) {
    a06.checks.push({
      id: 'A06-ROUTES',
      name: 'Route Definitions & Catalog',
      status: 'PASS',
      severity: 'PASS',
      message: `Route definitions or controller catalog detected (${routesLocation})`
    });
  } else {
    a06.checks.push({
      id: 'A06-ROUTES',
      name: 'Route Definitions & Catalog',
      status: 'WARN',
      severity: 'WARNING',
      message: 'No route definitions, controller directories, or API endpoints detected'
    });
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Calculate Totals & Summary
  // ──────────────────────────────────────────────────────────────────────────
  let total = 0;
  let passed = 0;
  let warnings = 0;
  let critical = 0;

  for (const contract of Object.values(report.contracts)) {
    for (const check of contract.checks) {
      total++;
      if (check.severity === 'CRITICAL' || check.status === 'FAIL') {
        critical++;
      } else if (check.severity === 'WARNING' || check.status === 'WARN') {
        warnings++;
      } else {
        passed++;
      }
    }
  }

  report.summary.total = total;
  report.summary.passed = passed;
  report.summary.warnings = warnings;
  report.summary.critical = critical;

  return report;
}

/**
 * Format terminal report.
 */
function renderTerminalReport(report, strict) {
  const lines = [];
  lines.push('================================================================================');
  lines.push('TECHNICAL CONTRACTS AUDIT REPORT');
  lines.push(`Target: ${report.target}`);
  lines.push(`Timestamp: ${report.timestamp}`);
  lines.push('Mode: Technical Contracts Gate (Zero-Dependency)');
  lines.push('================================================================================');
  lines.push('');

  for (const contract of Object.values(report.contracts)) {
    lines.push(`[${contract.id}] ${contract.name}`);
    for (const check of contract.checks) {
      let icon = '[PASS]';
      if (check.severity === 'CRITICAL' || check.status === 'FAIL') {
        icon = '[FAIL]';
      } else if (check.severity === 'WARNING' || check.status === 'WARN') {
        icon = '[WARN]';
      }
      lines.push(`  ${icon} ${check.name}: ${check.message}`);
    }
    lines.push('');
  }

  lines.push('================================================================================');
  lines.push(`Summary: ${report.summary.passed} passed, ${report.summary.warnings} warning(s), ${report.summary.critical} critical failure(s)`);

  let passedVerdict = false;
  if (report.summary.critical > 0) {
    lines.push('Result: FAILED (Critical checks failed)');
    passedVerdict = false;
  } else if (strict && report.summary.warnings > 0) {
    lines.push('Result: FAILED (Strict mode: warnings treated as errors)');
    passedVerdict = false;
  } else {
    lines.push('Result: PASSED (All critical checks satisfied)');
    passedVerdict = true;
  }
  lines.push('================================================================================');

  return { text: lines.join('\n'), passed: passedVerdict };
}

/**
 * CLI parser and runner.
 */
function main() {
  const args = process.argv.slice(2);
  let cwd = '.';
  let strict = false;
  let jsonOutput = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--cwd') {
      cwd = args[++i] || '.';
    } else if (arg === '--strict') {
      strict = true;
    } else if (arg === '--json') {
      jsonOutput = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: node scripts/audit_api_contracts.js [OPTIONS]

Deterministic technical contracts auditor with zero external dependencies.

Options:
  --cwd <path>  Target directory to audit (default: ".")
  --strict      Treat warnings as errors (exit code 1 if any warning)
  --json        Output report as JSON
  --help, -h    Show this help message
`);
      process.exit(0);
    }
  }

  const report = auditTechnicalContracts(cwd);
  const { text, passed } = renderTerminalReport(report, strict);

  if (jsonOutput) {
    report.summary.verdict = passed ? 'PASSED' : 'FAILED';
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(text);
  }

  process.exit(passed ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = {
  auditTechnicalContracts,
  renderTerminalReport
};
