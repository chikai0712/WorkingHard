#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import https from 'node:https';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import axios from 'axios';
import chalk from 'chalk';
import { faker } from '@faker-js/faker';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

const DEFAULT_BASE_URL =
  process.env.SENTINEL_URL || 'https://sentinel-api-demo.568win.com';
const DEFAULT_DISTIL_KEY = process.env.DISTIL_KEY || 'FV8d29SwmQ2T4bHKL1hABvtqu8AGs7GT';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const argv = yargs(hideBin(process.argv))
  .scriptName('creep-load-test')
  .usage('$0 [options]')
  .option('base-url', {
    alias: 'b',
    type: 'string',
    describe: 'Sentinel backend base URL',
    default: DEFAULT_BASE_URL,
  })
  .option('distil-key', {
    alias: 'k',
    type: 'string',
    describe: 'Distil encryption key (falls back to env DISTIL_KEY)',
    default: DEFAULT_DISTIL_KEY,
  })
  .option('accounts-file', {
    alias: 'f',
    type: 'string',
    describe: 'Path to JSON/NDJSON file that lists account IDs',
  })
  .option('accounts', {
    alias: 'a',
    type: 'string',
    describe: 'Comma separated list of account IDs to replay',
  })
  .option('accounts-count', {
    type: 'number',
    describe: 'Number of synthetic accounts to generate when none provided',
    default: 5,
  })
  .option('duration', {
    alias: 'd',
    type: 'number',
    describe: 'Duration of the test in seconds',
    default: 60,
  })
  .option('concurrency', {
    alias: 'c',
    type: 'number',
    describe: 'Number of concurrent workers',
    default: 4,
  })
  .option('target-rps', {
    alias: 'r',
    type: 'number',
    describe: 'Approximate aggregate requests per second',
    default: 20,
  })
  .option('timeout', {
    type: 'number',
    describe: 'HTTP timeout per request (ms)',
    default: 5000,
  })
  .option('cdn-test-ratio', {
    type: 'number',
    describe: 'Probability (0-1) of hitting /Receive/CdnTest instead of /Receive',
    default: 0.15,
  })
  .option('cdn-names', {
    type: 'string',
    describe: 'Comma separated CDN names to randomize in CDN results',
    default: 'akamai,cloudfront,fastly,quantil,cloudflare',
  })
  .option('dry-run', {
    type: 'boolean',
    describe: 'Generate one payload and print it without sending',
    default: false,
  })
  .option('insecure', {
    type: 'boolean',
    describe: 'Allow self-signed TLS certificates',
    default: true,
  })
  .option('verbose', {
    type: 'boolean',
    describe: 'Enable verbose logging for each request',
    default: false,
  })
  .option('plan-name', {
    type: 'string',
    describe: 'Label for the run (appears in logs)',
    default: 'default-plan',
  })
  .help()
  .alias('h', 'help')
  .strict()
  .parseSync();

function assertKey(key) {
  if (!key || key.length < 32) {
    throw new Error('Distil key must be at least 32 characters long');
  }
  return key.slice(0, 32);
}

function deflatePayload(payload) {
  return zlib.deflateSync(Buffer.from(payload, 'utf8'));
}

function encryptVisitorCookie(visitorJson, distilKey) {
  const key = Buffer.from(assertKey(distilKey), 'utf8');
  const iv = crypto.randomBytes(16);
  const compressed = deflatePayload(visitorJson);
  const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
  const encrypted = Buffer.concat([cipher.update(compressed), cipher.final()]);
  return `1:${iv.toString('base64')}:${encrypted.toString('base64')}`;
}

function buildVisitorFingerprint(accountId) {
  const now = new Date();
  return {
    action: faker.helpers.arrayElement(['allow', 'challenge', 'reject']),
    AccountId: accountId,
    'interrogator-timestamp': now.toISOString(),
    'client-platform': faker.internet.userAgent(),
    expires: Math.floor(Date.now() / 1000) + faker.number.int({ min: 60, max: 600 }),
    fingerprint: faker.string.uuid(),
    flags: faker.helpers.arrayElements(
      ['automation', 'multiple-logins', 'vpn', 'velocity', 'geo'],
      faker.number.int({ min: 0, max: 3 })
    ),
    fpid: faker.string.alphanumeric({ length: 32 }),
    'header-id': faker.string.alphanumeric({ length: 24 }),
    'primitive-id': faker.string.alphanumeric({ length: 20 }),
    'random-id': faker.string.alphanumeric({ length: 28 }),
    'site-id': faker.string.alpha({ length: 8 }),
    tags: faker.helpers.arrayElements(['sbobet', 'hk', 'vip', 'abtest'], faker.number.int({ min: 0, max: 3 })),
    version: faker.number.int({ min: 80, max: 90 }),
    'visitor-ip': faker.internet.ipv4(),
    zid: faker.string.alphanumeric({ length: 10 }),
    zuid: faker.string.alphanumeric({ length: 12 }),
    ModifiedBy: 'creep-loadtest',
    CreatedBy: 'creep-loadtest',
  };
}

function buildVisitorEnvelope(accountId, distilKey) {
  const fingerprint = buildVisitorFingerprint(accountId);
  const visitorJson = JSON.stringify(fingerprint);
  const visitorId = encryptVisitorCookie(visitorJson, distilKey);
  return { fingerprint, visitorId };
}

function buildCdnResultPayload(accountId, visitorId, cdnNames) {
  const results = cdnNames.map((name) => {
    const success = faker.datatype.boolean({ probability: 0.85 });
    return {
      name,
      responseTimeMs: faker.number.float({ min: 20, max: 800, multipleOf: 0.01 }),
      success,
      error: success ? null : faker.helpers.arrayElement(['Timeout', 'HTTP 500', 'Connection reset']),
    };
  });

  const fastest = results
    .filter((r) => r.success)
    .sort((a, b) => a.responseTimeMs - b.responseTimeMs)[0]?.name ?? cdnNames[0];

  return {
    accountId,
    visitorId,
    fastestCdn: fastest,
    results,
  };
}

async function loadAccounts() {
  if (argv.accounts) {
    return argv.accounts
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  if (argv['accounts-file']) {
    const fullPath = path.isAbsolute(argv['accounts-file'])
      ? argv['accounts-file']
      : path.join(__dirname, argv['accounts-file']);
    const raw = await fs.readFile(fullPath, 'utf8');
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed.map((value) => String(value)).filter(Boolean);
      }
    } catch {
      // fall through to NDJSON parsing
    }
    return raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  }

  return Array.from({ length: argv['accounts-count'] }, () => faker.internet.username());
}

function percentile(samples, pct) {
  if (!samples.length) return 0;
  const sorted = [...samples].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.floor((pct / 100) * sorted.length));
  return sorted[idx];
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatMs(ms) {
  return `${ms.toFixed(1)}ms`;
}

function summarizeLatencies(samples) {
  if (!samples.length) return 'n/a';
  return [
    `avg=${formatMs(samples.reduce((a, b) => a + b, 0) / samples.length)}`,
    `p50=${formatMs(percentile(samples, 50))}`,
    `p95=${formatMs(percentile(samples, 95))}`,
    `max=${formatMs(Math.max(...samples))}`,
  ].join(' ');
}

async function main() {
  const accounts = await loadAccounts();
  if (!accounts.length) {
    throw new Error('No accounts available. Pass --accounts, --accounts-file, or increase --accounts-count.');
  }

  const distilKey = argv['distil-key'] || DEFAULT_DISTIL_KEY;
  const cdnNames = argv['cdn-names'].split(',').map((name) => name.trim()).filter(Boolean);
  const httpsAgent = argv.insecure
    ? new https.Agent({
        rejectUnauthorized: false,
      })
    : undefined;

  axios.defaults.baseURL = argv['base-url'];
  axios.defaults.timeout = argv.timeout;
  if (httpsAgent) {
    axios.defaults.httpsAgent = httpsAgent;
  }

  console.log(chalk.cyan(`▶ Starting plan "${argv['plan-name']}"`));
  console.log(
    chalk.gray(
      [
        `base=${argv['base-url']}`,
        `duration=${argv.duration}s`,
        `concurrency=${argv.concurrency}`,
        `targetRps=${argv['target-rps']}`,
        `cdnRatio=${argv['cdn-test-ratio']}`,
        `accounts=${accounts.length}`,
      ].join(' | ')
    )
  );

  if (argv['dry-run']) {
    const sampleAccount = accounts[0];
    const envelope = buildVisitorEnvelope(sampleAccount, distilKey);
    const cdnPayload = buildCdnResultPayload(sampleAccount, envelope.visitorId, cdnNames);
    console.log(chalk.green('Dry-run sample payloads:'));
    console.log(
      JSON.stringify(
        {
          receive: {
            accountId: sampleAccount,
            // Print full visitorId so it can be copied into manual tests
            visitorId: envelope.visitorId,
            fingerprint: envelope.fingerprint,
          },
          cdnTest: cdnPayload,
        },
        null,
        2
      )
    );
    return;
  }

  /** @type {{
      receive: { ok: number, fail: number, latencies: number[] },
      cdn: { ok: number, fail: number, latencies: number[] },
      errors: Array<Record<string, unknown>>
    }} */
  const metrics = {
    receive: { ok: 0, fail: 0, latencies: /** @type {number[]} */ ([]) },
    cdn: { ok: 0, fail: 0, latencies: /** @type {number[]} */ ([]) },
    errors: [],
  };

  const runUntil = Date.now() + argv.duration * 1000;
  const workerDelay =
    argv['target-rps'] > 0 ? (1000 * Math.max(1, argv.concurrency)) / argv['target-rps'] : 0;

  async function fireReceive(accountId) {
    const start = performance.now();
    const envelope = buildVisitorEnvelope(accountId, distilKey);
    const payload = {
      accountId,
      visitorId: envelope.visitorId,
    };

    try {
      const response = await axios.post('/api/Receive/Receive', payload, {
        validateStatus: () => true,
      });

      const duration = performance.now() - start;
      metrics.receive.latencies.push(duration);

      if (response.status >= 200 && response.status < 300) {
        metrics.receive.ok += 1;
        if (argv.verbose) {
          console.log(chalk.green(`[Receive] ${response.status} ${formatMs(duration)}`));
        }
      } else {
        metrics.receive.fail += 1;
        metrics.errors.push({
          endpoint: '/api/Receive/Receive',
          status: response.status,
          data: response.data,
        });
        if (argv.verbose) {
          console.warn(chalk.yellow(`[Receive] ${response.status} body=${JSON.stringify(response.data)}`));
        }
      }
    } catch (error) {
      metrics.receive.fail += 1;
      metrics.errors.push({
        endpoint: '/api/Receive/Receive',
        error: error.message,
      });
      if (argv.verbose) {
        console.error(chalk.red(`[Receive] exception=${error.message}`));
      }
    }
  }

  async function fireCdnTest(accountId) {
    const start = performance.now();
    const envelope = buildVisitorEnvelope(accountId, distilKey);
    const payload = buildCdnResultPayload(accountId, envelope.visitorId, cdnNames);

    try {
      const response = await axios.post('/api/Receive/CdnTest', payload, {
        validateStatus: () => true,
      });
      const duration = performance.now() - start;
      metrics.cdn.latencies.push(duration);

      if (response.status >= 200 && response.status < 300) {
        metrics.cdn.ok += 1;
        if (argv.verbose) {
          console.log(chalk.green(`[CdnTest] ${response.status} ${formatMs(duration)}`));
        }
      } else {
        metrics.cdn.fail += 1;
        metrics.errors.push({
          endpoint: '/api/Receive/CdnTest',
          status: response.status,
          data: response.data,
        });
        if (argv.verbose) {
          console.warn(chalk.yellow(`[CdnTest] ${response.status} body=${JSON.stringify(response.data)}`));
        }
      }
    } catch (error) {
      metrics.cdn.fail += 1;
      metrics.errors.push({
        endpoint: '/api/Receive/CdnTest',
        error: error.message,
      });
      if (argv.verbose) {
        console.error(chalk.red(`[CdnTest] exception=${error.message}`));
      }
    }
  }

  async function worker(workerId) {
    while (Date.now() < runUntil) {
      const accountId = faker.helpers.arrayElement(accounts);
      const scenario = Math.random();
      if (scenario < argv['cdn-test-ratio']) {
        await fireCdnTest(accountId);
      } else {
        await fireReceive(accountId);
      }

      if (workerDelay > 0) {
        await sleep(workerDelay);
      }
    }
    if (argv.verbose) {
      console.log(chalk.gray(`worker-${workerId} completed`));
    }
  }

  await Promise.all(Array.from({ length: argv.concurrency }, (_, idx) => worker(idx)));

  console.log(chalk.cyan('\n▶ Test summary'));
  console.log(
    chalk.gray(
      `Receive: ok=${metrics.receive.ok} fail=${metrics.receive.fail} | ${summarizeLatencies(
        metrics.receive.latencies
      )}`
    )
  );
  console.log(
    chalk.gray(
      `CdnTest: ok=${metrics.cdn.ok} fail=${metrics.cdn.fail} | ${summarizeLatencies(metrics.cdn.latencies)}`
    )
  );

  if (metrics.errors.length) {
    console.log(chalk.yellow(`\n⚠ ${metrics.errors.length} errors captured (showing up to 5):`));
    metrics.errors.slice(0, 5).forEach((err, idx) => {
      console.log(chalk.yellow(`#${idx + 1} ${JSON.stringify(err, null, 2)}`));
    });
  } else {
    console.log(chalk.green('\nNo errors recorded.'));
  }
}

main().catch((err) => {
  console.error(chalk.red(`Load test failed: ${err.message}`));
  process.exitCode = 1;
});


