package web

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"time"

	"github.com/0mit/daftar/daftard/internal/worker"
)

// ONE DAEMON PER GARDEN (the operator, 2026-10-14): a garden is answered only by its own daftard, which holds it. What
// the machine keeps once — the served handplace's listener, Odoo's origin — is kept by the machine's daftard, and each
// question it has for a garden is asked of that garden's daemon (POST /internal/call on its loopback address, the
// machine's key in a header), where it is answered as the garden's own pages are: from its memory where it can be.

// Caller answers a garden's questions: the garden's own worker in its daemon, or that daemon (Remote) in the machine's.
type Caller interface {
	Call(method string, params any, timeout time.Duration) (json.RawMessage, error)
	Close()
}

// Remote is a garden's daemon, asked from the machine's daftard.
type Remote struct {
	Garden string // the garden's name, as its daemon serves it
	Addr   string // its daemon's address on the loopback
	Token  string // the machine's key
}

// Call asks the garden's daemon; a refusal or a failure of the garden's worker comes back as the worker's own error.
func (rm *Remote) Call(method string, params any, timeout time.Duration) (json.RawMessage, error) {
	body, err := json.Marshal(map[string]any{"garden": rm.Garden, "method": method, "params": params,
		"timeout_ms": timeout.Milliseconds()})
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout+30*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "http://"+rm.Addr+"/internal/call", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set(keyHeader, rm.Token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, &worker.Error{Status: 503, Kind: "failed", Message: "the garden's daftard did not answer",
			Diagnostic: err.Error()}
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &worker.Error{Status: 503, Kind: "failed", Message: "the garden's daftard's answer broke off",
			Diagnostic: err.Error()}
	}
	if resp.StatusCode == http.StatusOK {
		return b, nil
	}
	var e struct {
		Error *worker.Error `json:"error"`
	}
	if json.Unmarshal(b, &e) == nil && e.Error != nil {
		return nil, e.Error
	}
	return nil, &worker.Error{Status: resp.StatusCode, Kind: "failed", Message: "the garden's daftard refused the question",
		Diagnostic: string(b[:min(len(b), 300)])}
}

// Close: the garden's daemon is its own, and ends with itself.
func (rm *Remote) Close() {}

// internalCall is POST /internal/call on a garden's daemon: the machine's daftard asking a question of this garden,
// the machine's key in a header. A question that reads is answered from memory where it can be (call); Odoo's calls
// are given the register's healthy routes here, where the routes are kept.
func (s *Server) internalCall(w http.ResponseWriter, r *http.Request) {
	if !same(r.Header.Get(keyHeader), s.Token) {
		reply(w, 403, map[string]any{"error": both("کلید معتبر نیست.", "The key is not valid.")})
		return
	}
	var req struct {
		Garden    string         `json:"garden"`
		Method    string         `json:"method"`
		Params    map[string]any `json:"params"`
		TimeoutMS int64          `json:"timeout_ms"`
	}
	if err := json.NewDecoder(io.LimitReader(r.Body, 256<<20)).Decode(&req); err != nil || req.Method == "" {
		reply(w, 400, map[string]any{"error": both("درخواست معتبر نیست.", "The request is not valid.")})
		return
	}
	var g *Garden
	for _, x := range s.Gardens {
		if x.Conf.Name == req.Garden {
			g = x
		}
	}
	if g == nil {
		reply(w, 404, map[string]any{"error": &worker.Error{Status: 404, Kind: "refused", Message: "this daftard serves no garden " + req.Garden}})
		return
	}
	timeout := time.Duration(req.TimeoutMS) * time.Millisecond
	if timeout <= 0 || timeout > 30*time.Minute {
		timeout = 2 * time.Minute
	}
	if req.Method == "odoo_rpc" && g.Register != nil {
		if req.Params == nil {
			req.Params = map[string]any{}
		}
		if _, given := req.Params["routes"]; !given {
			req.Params["routes"] = g.Register.Hand()
		}
	}
	raw, err := s.call(g, req.Method, req.Params, timeout)
	if err != nil {
		we, ok := worker.IsError(err)
		if !ok {
			we = &worker.Error{Status: 500, Kind: "failed", Message: err.Error()}
		}
		reply(w, 502, map[string]any{"error": we})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(raw)
}
