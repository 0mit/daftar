// Package served is the handplace served beyond this machine (design §10.1): for a person a grant opens a garden to,
// signed in, over TLS, each page and call asked of the garden's `may` before it is served (flow row `served`).
//
// DAFTARD KEEPS NO PASSWORD. A person signs in by a short-lived link sent to them through a channel the gardener
// granted (the garden's flow law lets a notice leave for that channel's party), to the address their own bean names; a
// passkey they register is the second way, to come. A link is good once, for a quarter of an hour; at most one is sent
// to a person a minute, and what is asked for a person nobody knows is answered as for one who is, so the page tells
// nobody who is kept here. A link begins a SESSION: one person in one garden, ended by signing out, after an hour with
// nothing done, or after twelve hours whatever is done. Only a token's digest is held, never the token itself.
package served

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"sync"
	"time"
)

// How long a link is good, how often one may be sent to a person, and how long a session lasts.
const (
	LinkLife  = 15 * time.Minute
	LinkEvery = time.Minute
	Idle      = time.Hour
	Life      = 12 * time.Hour
)

// Session is one person signed in to one garden.
type Session struct {
	Garden, Person string
	CSRF           string
	Since, last    time.Time
}

type link struct {
	garden, person string
	until          time.Time
}

// Sessions holds the links sent, the challenges a passkey answers and the sessions begun, each by its digest.
type Sessions struct {
	mu         sync.Mutex
	links      map[string]link
	sessions   map[string]*Session
	sent       map[string]time.Time // garden/person → when a link was last sent
	challenges map[string]challenge // a challenge's digest → what it was asked for, and until when, once
}

// ChallengeLife is how long a passkey's challenge may be answered.
const ChallengeLife = 5 * time.Minute

// Max is how many links, challenges and sessions are held at once, each: beyond it a stranger's request is answered
// alike and nothing more is kept (security audit 2026-10-10, 1.1).
const Max = 1000

// New holds nothing yet.
func New() *Sessions {
	return &Sessions{links: map[string]link{}, sessions: map[string]*Session{}, sent: map[string]time.Time{},
		challenges: map[string]challenge{}}
}

type challenge struct {
	purpose, session string // "signin" (no session), or "register" by the session that asked
	until            time.Time
}

// Challenge is a new challenge for a passkey to answer, once, within ChallengeLife, for what it was asked for:
// a sign-in, or a registration by one session (security audit 2026-10-10, 1.5). Past Max held at once, it is
// answered alike and kept nowhere, so it can be spent by nobody (1.1).
func (s *Sessions) Challenge(purpose, session string, now time.Time) []byte {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sweep(now)
	if len(s.challenges) < Max {
		s.challenges[digest(string(b))] = challenge{purpose: purpose, session: digest(session), until: now.Add(ChallengeLife)}
	}
	return b
}

// Spend takes a challenge back as answered: true once, while it lasts, for what it was asked for and by whom.
func (s *Sessions) Spend(ch []byte, purpose, session string, now time.Time) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	d := digest(string(ch))
	c, ok := s.challenges[d]
	delete(s.challenges, d)
	return ok && !now.After(c.until) && c.purpose == purpose && c.session == digest(session)
}

// Begin begins a session for a person whose passkey the garden names and who answered a challenge with it.
func (s *Sessions) Begin(garden, person string, now time.Time) (string, *Session) {
	s.mu.Lock()
	defer s.mu.Unlock()
	sid := token()
	se := &Session{Garden: garden, Person: person, CSRF: token(), Since: now, last: now}
	s.sessions[digest(sid)] = se
	return sid, se
}

func token() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err) // no randomness: nothing may be served
	}
	return base64.RawURLEncoding.EncodeToString(b)
}

func digest(t string) string {
	d := sha256.Sum256([]byte(t))
	return hex.EncodeToString(d[:])
}

// Issue is a new link's token for the person in the garden, and false where one was sent to them within LinkEvery.
func (s *Sessions) Issue(garden, person string, now time.Time) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sweep(now)
	key := garden + "/" + person
	if last, ok := s.sent[key]; ok && now.Sub(last) < LinkEvery {
		return "", false
	}
	if len(s.links) >= Max { // a stranger's flood keeps nothing more; the answer is the same (security audit 1.1)
		return "", false
	}
	s.sent[key] = now
	t := token()
	s.links[digest(t)] = link{garden: garden, person: person, until: now.Add(LinkLife)}
	return t, true
}

// Redeem begins a session by a link's token, once: the session's own token and the session, or false where the link
// is unknown, used, or past its quarter of an hour.
func (s *Sessions) Redeem(t string, now time.Time) (string, *Session, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sweep(now)
	d := digest(t)
	l, ok := s.links[d]
	if !ok || now.After(l.until) {
		return "", nil, false
	}
	delete(s.links, d)
	sid := token()
	se := &Session{Garden: l.garden, Person: l.person, CSRF: token(), Since: now, last: now}
	s.sessions[digest(sid)] = se
	return sid, se, true
}

// Get is the session a cookie's token names, while it lasts; each call is something done in it.
func (s *Sessions) Get(sid string, now time.Time) (*Session, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	se, ok := s.sessions[digest(sid)]
	if !ok || now.Sub(se.last) > Idle || now.Sub(se.Since) > Life {
		delete(s.sessions, digest(sid))
		return nil, false
	}
	se.last = now
	return se, true
}

// End ends the session a token names.
func (s *Sessions) End(sid string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.sessions, digest(sid))
}

func (s *Sessions) sweep(now time.Time) {
	for d, l := range s.links {
		if now.After(l.until) {
			delete(s.links, d)
		}
	}
	for k, t := range s.sent {
		if now.Sub(t) >= LinkEvery {
			delete(s.sent, k)
		}
	}
	for d, se := range s.sessions {
		if now.Sub(se.last) > Idle || now.Sub(se.Since) > Life {
			delete(s.sessions, d)
		}
	}
	for d, c := range s.challenges {
		if now.After(c.until) {
			delete(s.challenges, d)
		}
	}
}
