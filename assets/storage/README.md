# storage — where each content is kept, what its keepings leave open, and what each transfer still has to do

`storage` is the asset of the `storage` profile. A garden that takes the profile (VOCAB.md `profiles: [storage]`, a
RULE-CHANGE the gardener ratifies) receives it at `assets/storage/`, and a garden that leaves the profile has it taken
away. Its files are the release's: an edit to one is a RULE-CHANGE, as an edit to any tool the release ships is.

It opens no concept of its own. What it reads is the law's: a carrier holds a volume, a folder holds a content under a
name (`hold … as`), two names of one inode hold it through the volume's one holding of it (`hold … through`), a copy is
a holding made from the holding it copies (`make … from`), a tree's manifest is its files' checksum lines and a dataset
the content of a manifest (core/law/formats.yaml `checksums`). The profile adds the keeping properties a reading can
read of a content's keepings (core/law/profiles.yaml `keeping_properties`), a garden's own risks, each the ways of
keeping that resolve it (VOCAB.md `risks`), the form `keep` of a policy scheme — the risks its members must be safe
against — and the groupings `keepings`, `datasets` and `events` (core/law/lines.yaml). It stores nothing it can read:
whether a content is safe is read each time, never written.

## A garden's risks and its policy

    # VOCAB.md
    risks:
      - { risk: disk-fault, meaning: "a disk stops reading", resolved_by: [ { disk: 2 }, { array: 1 } ] }
      - { risk: malice, meaning: "a program writes over every disk it can reach", resolved_by: [ { offline: 1 }, { immutable: 1 } ] }

    # extracts/keep.tsv, a scheme of the form `keep`
    code         level  name                    covers               within  for
    precious     code   kept against all        disk-fault malice    365 d   media:captured-raw
    replaceable  code   none needed

A root is classed by a person (`classify: { of: store:folder:<id>, as: keep:precious }`); what is beneath it inherits
the code, and a content no root classes is read under the code whose `for` names a code it holds. Where nothing
classes a content, its keepings are read for what they resolve, and it is judged against nothing.

## What it reads

    python3 assets/storage/bin/storage.py keepings --scheme keep [--of <folder or content>] [--json]
    python3 assets/storage/bin/storage.py datasets [--of <folder>] [--same]
    python3 assets/storage/bin/storage.py events --of <volume or folder> --gap "36 h"
    python3 assets/storage/bin/storage.py manifest <folder> > tree.b3      # `b3sum --check tree.b3` in the folder

Each reads the store a host keeps (`--store`, or the one it keeps) in one snapshot, and the garden's beans for what a
person says: a disk's place (`be … as: location`), that it is part of a host (attached), the keys a carrier needs
(`need … of`) and who holds them (`hold … of`, never the key itself). `keepings` prints, per policy code, how many
contents and bytes leave which risks open and what would close each — "disk-fault: 1 more keeping on another disk".

## Transfers

    python3 assets/storage/bin/transfer.py setup --by <being>     # mappings/walk-transfer.md, the walk
    python3 assets/storage/bin/transfer.py start --store S --to <being> --dataset <blake3> --from <being> --total N
    python3 assets/storage/bin/transfer.py move <course> copying --done N --store S
    python3 assets/storage/bin/transfer.py show --store S

A copy, a move or a verification is a course on `walk-transfer` (queued, copying, verifying, then done; paused; failed
or stopped), of the being it fills, needing the dataset it is to hold and meeting the need when every content is found
whole there. Its work is done by runs (`daftar run`); the course outlives them, and a page shows its step and how far
it has come.

## Containers

    python3 assets/storage/bin/container.py list <archive> --index <out.sqlite> [--passphrase-stdin]

An archive or a cabinet (zip, with ZipCrypto and AES; tar and its compressions; 7z; rar 4; cab; iso 9660) is read as
a volume: its members listed and each hashed by BLAKE3 as it streams, never unpacked to disk, into an index of the
shape a scan writes, which `daftar import file-tree` reads with the container's content as the volume's carrier. A
passphrase comes on standard input from a pipe — a wallet's query — never on a command line or in a file; a member
that needs one none was given for is listed without its digest, and the exit code 3 says so. A path that climbs out of
the container is kept by its name alone, and said.

Dependencies: none beyond the release's for the readings; `python-libarchive-c` and `blake3` (pip) for a container,
and 7-Zip for an encrypted 7z or a rar 5.
