// node test/toolbox/release.test.mjs — the toolbox's copies of the release's own widgets, held to the release: a file the
// toolbox keeps as the release's (daftar's assets/view/lib/widgets, which daftard serves a garden at
// /release/<garden>/widgets/…) is that file byte for byte, never edited here. DAFTAR names the daftar tree to hold it
// to, as for the Go tests that read daftar's own files; with none named, it says so and checks nothing.
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const SAME = ['direction.js'];          // the release's, byte for byte; the rest of the toolbox has drifted (P1)
const tree = process.env.DAFTAR;
if (!tree) {
  console.log('SKIP: release — DAFTAR names no daftar tree to hold the toolbox to');
  process.exit(0);
}
const lib = join(tree, 'assets', 'view', 'lib', 'widgets');
const missing = SAME.filter(f => !existsSync(join(lib, f)));
if (missing.length) {
  console.log(`FAIL: release — ${tree} holds no ${missing.map(f => 'assets/view/lib/widgets/' + f).join(', ')}: ` +
              'name a daftar tree whose release carries it');
  process.exit(1);
}
const drifted = SAME.filter(f => !readFileSync(new URL(`../../web/toolbox/${f}`, import.meta.url)).equals(readFileSync(join(lib, f))));
if (drifted.length) {
  console.log(`FAIL: release — ${drifted.join(', ')} is not ${tree}'s, byte for byte: copy the release's again, never edit it here`);
  process.exit(1);
}
console.log(`PASS: release — ${SAME.join(', ')}: the release's own, byte for byte (${lib})`);
