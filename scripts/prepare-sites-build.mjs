import { mkdir, readdir, rename } from 'node:fs/promises';
import { resolve } from 'node:path';

const distDirectory = resolve('dist');
const clientDirectory = resolve(distDirectory, 'client');
const reservedEntries = new Set(['.openai', 'client', 'server']);

await mkdir(clientDirectory, { recursive: true });

for (const entry of await readdir(distDirectory)) {
  if (reservedEntries.has(entry)) continue;
  await rename(resolve(distDirectory, entry), resolve(clientDirectory, entry));
}
