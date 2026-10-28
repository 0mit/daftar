// Package python carries python/garden_worker.py inside daftard; it is written into the state folder at start and run
// with each garden's own Python.
package python

import _ "embed"

//go:embed garden_worker.py
var Worker []byte

// Modules are the worker's own modules, written beside it: name → its text.
//
//go:embed odoo_rpc.py
var odooRPC []byte

//go:embed register.py
var register []byte

// Modules the worker imports from its own folder.
var Modules = map[string][]byte{"odoo_rpc.py": odooRPC, "register.py": register}
