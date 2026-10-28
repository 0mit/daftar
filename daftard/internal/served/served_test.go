package served

import (
	"strings"
	"testing"
	"time"
)

// A LINK IS GOOD ONCE, FOR A QUARTER OF AN HOUR; one a minute to a person; a session lasts while something is done in it
// within the hour, and twelve hours at most; only digests are held.
func TestLinksAndSessions(t *testing.T) {
	s := New()
	now := time.Date(2026, 10, 9, 12, 0, 0, 0, time.UTC)
	tok, ok := s.Issue("g", "ana", now)
	if !ok || len(tok) < 40 {
		t.Fatalf("a link is issued: %q %v", tok, ok)
	}
	if _, ok := s.Issue("g", "ana", now.Add(30*time.Second)); ok {
		t.Fatalf("a second link to the same person within the minute is not sent")
	}
	if _, ok := s.Issue("g", "ben", now.Add(30*time.Second)); !ok {
		t.Fatalf("another person's link is theirs to have")
	}
	for d := range s.links {
		if strings.Contains(d, tok) || d == tok {
			t.Fatalf("only a token's digest is held")
		}
	}
	sid, se, ok := s.Redeem(tok, now.Add(time.Minute))
	if !ok || se.Person != "ana" || se.Garden != "g" || sid == "" || se.CSRF == "" {
		t.Fatalf("the link begins her session: %v %v", se, ok)
	}
	if _, _, ok := s.Redeem(tok, now.Add(2*time.Minute)); ok {
		t.Fatalf("a link is good once")
	}
	if got, ok := s.Get(sid, now.Add(50*time.Minute)); !ok || got.Person != "ana" {
		t.Fatalf("the session lasts while something is done in it")
	}
	if _, ok := s.Get(sid, now.Add(50*time.Minute+Idle+time.Second)); ok {
		t.Fatalf("an hour with nothing done ends it")
	}
	late, _ := s.Issue("g", "ana", now.Add(3*time.Minute))
	if _, _, ok := s.Redeem(late, now.Add(3*time.Minute+LinkLife+time.Second)); ok {
		t.Fatalf("a link past its quarter of an hour begins nothing")
	}
	t2, _ := s.Issue("g", "ana", now.Add(10*time.Minute))
	sid2, _, _ := s.Redeem(t2, now.Add(10*time.Minute))
	begun, at, ended := now.Add(10*time.Minute), now.Add(10*time.Minute), false
	for i := 0; i < 14 && !ended; i++ { // something done every 55 minutes, and still ended at twelve hours
		at = at.Add(55 * time.Minute)
		_, ok := s.Get(sid2, at)
		ended = !ok
		if ended != (at.Sub(begun) > Life) {
			t.Fatalf("at %v a session in use is ended=%v: it lasts twelve hours, and no longer", at.Sub(begun), ended)
		}
	}
	if !ended {
		t.Fatalf("a session in use was never ended")
	}
	t3, _ := s.Issue("g", "ben", now.Add(20*time.Minute))
	sid3, _, _ := s.Redeem(t3, now.Add(20*time.Minute))
	s.End(sid3)
	if _, ok := s.Get(sid3, now.Add(20*time.Minute)); ok {
		t.Fatalf("signing out ends the session")
	}
}
