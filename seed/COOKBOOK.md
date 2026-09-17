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
required on every `kind: domain` bean.

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

The provider owns the machine and Sam answers for what runs on it. With no hardware to read, it is
anchored on its name.

<!-- example: beans/vps-a.md -->
```markdown
---
bean: vps-a
kind: host
title: "vps-a — a rented virtual server"
status: active
summary: "A VPS rented from a hosting provider."
nature: physical
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
(`CONTRIBUTING.md`). `values_add` appends to the standard list, and `registry_additions` adds the matching
registry row, so the garden accounts only for what it added.

Add this inside `VOCAB.md`'s front matter:

<!-- example-front-matter: VOCAB.md -->
```yaml
local_terms:
  - term: os
    schema: { values_add: [nas-os] }
registry_additions:
  operating_systems:
    - { os: nas-os, family: unix, path_grammar: unix-filesystem, meaning: "A vendor's Linux-based NAS operating system." }
```

Then the NAS bean can say `os: nas-os`. (The germinated `VOCAB.md` already has an empty `local_terms: []`
line; replace it with the block above rather than adding a second `local_terms:` — the gate refuses a key
written twice.)
