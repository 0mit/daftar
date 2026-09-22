# Cookbook — the common things, written the way the gate accepts them

Every block marked `<!-- example: … -->` below is **committed into a freshly grown garden by
`test/germinate.py`**, together with the person `sam` from `seed/README.md`. If the law moves and one stops
passing, that test fails — so these are not illustrations that can quietly go stale.

The scenario: Sam registers `example.org`, keeps a NAS at home that serves the website for it, and rents a
VPS.

## How to say that one thing relates to another

Pick the most specific relation that is true; `refs` is the open fallback.

| you want to say | write | notes |
|---|---|---|
| who owns it, and who answers for it | `owned_by` + `responsibility` | always both, facet by facet (`legal`, `technical`) |
| something outside this ledger owns it | `owned_by: { legal: { external: "…" } }` | a rented VPS, third-party software, a registered domain |
| a running thing sits on a machine | `lives_in: { bean: … }` | the machine must say what habitat it offers (`provides_habitat`) |
| a running thing is a copy of some software | `instance_of: { bean: … }` | required on `kind: instance`, together with `lives_in` |
| it cannot work without another thing | `depends_on: { <name>: { bean: … } }` | must stay acyclic |
| anything else — "serves", "is DNS for", "backs up" | `refs: { <slot>: { bean: …, rel: <kebab-verb> } }` | `rel` is free text, so a new relation needs no rule change |

Anchors say what an object IS, so two gardens recognise the same thing. A machine is best anchored on
hardware (a serial or a MAC); a rented machine you cannot touch on its name (`fqdn`); a domain on its `fqdn`;
software or a deployment on a logical id you choose (`product_id`, `service_id`). A person uses a logical id
(`person_id`) — never their name.

## A registered domain

A domain is registered for a term, not owned outright, so the registry is the `external` owner and the
person who renews it answers for it. Registration facts belong to the opt-in **`domain` profile**: a garden
that holds domains adds this inside `VOCAB.md`'s front matter, and `registration` then becomes available and
required on every `kind: domain` bean. Its dates are read from WHOIS before the bean is written: `created` and
`expires` take a date and nothing else — there is no `unknown` for a fact that is always there to be read, and
an invented date would pass the gate and then be reported as sound by `dmstale`. `auto_renew` alone may be
`unknown`, because it is an account setting WHOIS does not show.

<!-- example-front-matter: VOCAB.md -->
```yaml
extends_profiles: [domain]
```

<!-- example: beans/example-org.md -->
```markdown
---
bean: example-org
kind: domain
title: "example.org — Sam's domain"
status: active
summary: "The domain Sam's website answers on."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the .org registry, under a registration agreement" } }
responsibility: { legal: { holder: { bean: sam } } }
registration:
  registrar: "Example Registrar Inc."
  created: 2020-01-15
  expires: 2027-01-15
  auto_renew: enabled
  observed: 2026-09-17
  source: "WHOIS for example.org, read 2026-09-17"
---
Sam's domain.
```

## A machine at home that other things run on

`provides_habitat` is what lets something `lives_in` it. `roles` says what the machine does — a list,
because a machine does several things.

<!-- example: beans/nas.md -->
```markdown
---
bean: nas
kind: host
title: "nas — Sam's home NAS"
status: active
summary: "A NAS at home: file storage, and the web server for example.org."
nature: physical
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "NAS-0042", class: hardware, establishing: true }
    - { key: hostname, value: "nas", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { owner: { bean: sam } }, technical: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } }, technical: { holder: { bean: sam } } }
provides_habitat: linux-baremetal
roles:
  - { role: file-server }
  - { role: web }
---
The NAS.
```

## Third-party software, and a running copy of it that serves the website

The software is a `product` owned by its authors; the running copy is an `instance` of it that lives on
the NAS and is Sam's. "Serves this domain" has no dedicated relation, so it is a `refs` entry with a `rel`.

<!-- example: beans/nginx.md -->
```markdown
---
bean: nginx
kind: product
title: "nginx — the web server software"
status: active
summary: "Third-party web server software, run here but owned by its project."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: product_id, value: "product:nginx", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the nginx project" } }
responsibility: { legal: { holder: { bean: sam } } }
---
The web server software.
```

<!-- example: beans/website.md -->
```markdown
---
bean: website
kind: instance
title: "website — nginx on the NAS, serving example.org"
status: active
summary: "The web server instance on the NAS that answers for example.org."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "nginx:example.org@nas", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
instance_of: { bean: nginx }
lives_in: { bean: nas }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
refs:
  domain: { bean: example-org, rel: serves }
---
The website.
```

## A rented VPS

A virtual machine has no matter of its own: it is a `virtual-host`, a living being that lapses at teardown,
identified by its name or by the id its provider assigns — never by a serial, which is the hypervisor's. The
provider owns it and Sam answers for what runs on it.

<!-- example: beans/vps-a.md -->
```markdown
---
bean: vps-a
kind: virtual-host
title: "vps-a — a rented virtual server"
status: active
summary: "A VPS rented from a hosting provider."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "vps-a.example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the hosting provider, which owns and operates the machine" } }
responsibility: { legal: { holder: { bean: sam } } }
provides_habitat: linux-vm
---
The rented server.
```

## A value the vocabulary does not have yet

The standard list of operating systems has no entry for the NAS's vendor OS. Do not bend the bean to fit:
add the value **for this garden** in `VOCAB.md`, and propose it upstream if others will need it
(`CONTRIBUTING.md`). Operating systems are a **registry**, and `os` reads its values from it, so the value is
added as a row — once, with everything a row carries — and the garden accounts only for the row it added.

Add this inside `VOCAB.md`'s front matter:

<!-- example-front-matter: VOCAB.md -->
```yaml
registry_additions:
  operating_systems:
    - { os: nas-os, family: unix, path_grammar: unix-filesystem, meaning: "A vendor's Linux-based NAS operating system." }
```

Then the NAS bean can say `os: nas-os`. **Commit the two together:** a value the garden adds must be used
by a bean, so the vocabulary change on its own is refused ("declared but NO bean occupies it"). The one
commit is one logical change — adding the thing and the value that describes it. If a later daftar release
adds the same value to the standard, the gate tells you to delete your local copy.

A term that carries its own closed list — `python3 bin/dmrules.py` shows which — takes the value with
`schema: { values_add: [...] }` in a `local_terms` entry instead; on a term that reads a registry, `values_add`
adds nothing. The gate's refusal of an unknown value says which of the two the term needs. (A germinated
`VOCAB.md` already has an empty `local_terms: []` line; replace it rather than adding a second — the gate
refuses a key written twice.)

## A kind of fact the standard has no term for

Keep it in `details:` until it recurs. When it does, give it a term **in this garden** — a term is data, so
the gate enforces it the moment it is written, with no code anywhere. Each attribute says ONE thing: what it
is a position `in:`, whether it is `required`, and what it `meaning`s. `python3 bin/dmrules.py` lists what
`in:` may say (`schema_language.attr_domains`): a closed list, a registry, an aspect, a value type, a pattern,
`extent`, `ref` — or `prose`, for a reason or a remark, which is deliberately not a position.

<!-- example-term: VOCAB.md -->
```yaml
local_terms:
  - term: rental
    meaning: "what a rented machine is rented from, and when the rent next falls due"
    context_keys: [rental]
    schema:
      shape: mapping
      attrs:
        provider: { required: true, in: prose,              meaning: "who it is rented from" }
        renews:   { required: true, in: { type: iso_date }, meaning: "ABSOLUTE date the next payment is due" }
        note:     { in: prose,                              meaning: "optional remark" }
    merge: { cardinality: single, order: none }
```

Then a bean can carry `rental: { provider: "a hosting company", renews: 2027-01-15 }`, and a bean that writes
`rental: { provider: "x", renews: "next January" }` — or adds a key the term does not declare — is refused. An
attribute whose `in:` is a closed list declares POSITIONS, and the gate will ask that each be used by a bean or
declared vacant with a reason. If the term proves general, propose it (`CONTRIBUTING.md`).

## Say what a thing is, in the world's shared terms (`knowledge` profile)

Opt in with `extends_profiles: [knowledge]` in VOCAB.md. Then:

```yaml
# a third-party product that IS a technology: anchor it, so every garden's "samba" is one object
identity: { status: confirmed, anchors: [ { key: technology, value: samba, class: logical, establishing: true } ] }
# anything may say what it stands on
knowledge:
  - { scheme: technology,   code: samba, rel: uses }
  - { scheme: isced-f-2013, code: "0612", rel: draws_on, topic: "network file sharing" }
  - { scheme: isco-08,      code: "2522", rel: classified_as }
```

`python3 bin/dmknowledge.py find <word>` finds a code; `show <scheme> <code>` shows its ancestry and, for a
technology, its official documentation.

