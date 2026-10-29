'use strict';

const fs = require('node:fs');
const path = require('node:path');

const TRANSIENT_FILES = new Set([
  'singletonlock', 'singletonsocket', 'singletoncookie', 'devtoolsactiveport',
]);

function shouldCopy(source) {
  const name = path.basename(source).toLowerCase();
  if (TRANSIENT_FILES.has(name)) return false;
  // Chromium stores HTTP, code, shader and GPU caches in several version-dependent folders.
  // Local Storage, IndexedDB, preferences, cookies and game settings are retained.
  return !(fs.lstatSync(source).isDirectory() && name.includes('cache'));
}

function exists(file) {
  try {
    fs.lstatSync(file);
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

function requireAbsolute(value, label) {
  if (typeof value !== 'string' || !path.isAbsolute(value)) {
    throw new Error(`${label} must be an absolute path.`);
  }
  return path.resolve(value);
}

/**
 * Select the still-running profile, or migrate it before Electron opens a browser session.
 * The pending JSON is task-created metadata, not a path supplied by game content.
 */
function preparePendingProfile({ pendingPath, defaultProfile, isProcessAlive }) {
  pendingPath = requireAbsolute(pendingPath, 'Pending metadata path');
  defaultProfile = requireAbsolute(defaultProfile, 'Default profile path');
  if (!exists(pendingPath)) return { profile: defaultProfile, pending: false };

  const pending = JSON.parse(fs.readFileSync(pendingPath, 'utf8'));
  if (pending.completed === true) {
    if (pending.destination && path.resolve(pending.destination) !== defaultProfile) {
      throw new Error('The completed profile migration belongs to another destination.');
    }
    return { profile: defaultProfile, pending: false };
  }

  const source = requireAbsolute(pending.source, 'Pending source profile');
  if (!path.basename(source).startsWith('azeroth-mac-')
      || !fs.lstatSync(source).isDirectory()) {
    throw new Error('The pending source must be an existing azeroth-mac- profile directory.');
  }
  if (source === defaultProfile) throw new Error('Source and destination profiles must differ.');
  if (!Number.isSafeInteger(pending.pid) || pending.pid <= 0) {
    throw new Error('The pending profile process ID is invalid.');
  }
  if (typeof isProcessAlive !== 'function') {
    throw new Error('A process-liveness check is required before migrating a profile.');
  }

  if (isProcessAlive(pending.pid)) return { profile: source, pending: true };

  if (exists(path.join(defaultProfile, 'Local Storage'))) {
    throw new Error('The default profile already contains Local Storage. Existing player data will not be overwritten.');
  }
  if (exists(defaultProfile)) {
    const destination = fs.lstatSync(defaultProfile);
    if (!destination.isDirectory() || fs.readdirSync(defaultProfile).length !== 0) {
      throw new Error('The default profile is not empty. Existing files will not be overwritten.');
    }
  }

  // Build the copy beside its final destination so the directory commit is atomic.
  fs.mkdirSync(path.dirname(defaultProfile), { recursive: true });
  const staging = fs.mkdtempSync(path.join(path.dirname(defaultProfile), '.azeroth-profile-migration-'));
  const completionPath = `${pendingPath}.complete-${process.pid}-${path.basename(staging)}`;
  let committed = false;
  try {
    fs.cpSync(source, staging, {
      recursive: true,
      dereference: false,
      preserveTimestamps: true,
      errorOnExist: true,
      force: false,
      filter: shouldCopy,
    });
    const completed = {
      ...pending,
      completed: true,
      destination: defaultProfile,
      completedAt: new Date().toISOString(),
    };
    // Prepare this file before committing the directory, but do not mark the pending record
    // complete until the profile copy has reached its final destination successfully.
    fs.writeFileSync(completionPath, JSON.stringify(completed, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
    if (exists(path.join(defaultProfile, 'Local Storage'))) {
      throw new Error('Player data appeared in the default profile during migration; nothing will be overwritten.');
    }
    fs.renameSync(staging, defaultProfile);
    committed = true;
    fs.renameSync(completionPath, pendingPath);
    return { profile: defaultProfile, pending: false, migrated: true };
  } catch (error) {
    if (committed) {
      throw new Error(`The profile was copied to ${defaultProfile}, but the completion record could not be updated: ${error.message}`, { cause: error });
    }
    throw error;
  } finally {
    if (!committed) fs.rmSync(staging, { recursive: true, force: true });
    fs.rmSync(completionPath, { force: true });
  }
}

module.exports = { preparePendingProfile };
