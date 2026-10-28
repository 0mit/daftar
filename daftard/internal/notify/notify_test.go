package notify

import (
	"encoding/xml"
	"errors"
	"path/filepath"
	"strings"
	"testing"
)

func watcher(t *testing.T, leads *[]Lead, shown *[]Notice, fail *bool) *Watcher {
	return &Watcher{Garden: "home", Whose: "دفتر آنا", Path: filepath.Join(t.TempDir(), "notified.json"),
		Show: func(n Notice) error {
			if *fail {
				return errors.New("no desktop")
			}
			*shown = append(*shown, n)
			return nil
		},
		Leads: func() ([]Lead, error) { return *leads, nil }}
}

func TestEachLeadOnce(t *testing.T) {
	var shown []Notice
	fail := false
	leads := []Lead{{Kind: "pending", ID: "a", About: "یک تصمیم"}}
	w := watcher(t, &leads, &shown, &fail)
	w.Check()
	w.Check()
	if len(shown) != 1 || shown[0].URL != "daftar://go/home/pending/a" || !strings.HasPrefix(shown[0].Title, "دفتر آنا — ") {
		t.Fatalf("first check: %+v", shown)
	}
	leads = append(leads, Lead{Kind: "proposal", ID: "PROPOSAL-x", About: "از همسایه"})
	w.Check()
	if len(shown) != 2 || shown[1].URL != "daftar://go/home/proposal/PROPOSAL-x" {
		t.Fatalf("a new lead: %+v", shown)
	}
	// a restart remembers; a lead that went away and came back is new again
	w2 := watcher(t, &leads, &shown, &fail)
	w2.Path = w.Path
	w2.Check()
	if len(shown) != 2 {
		t.Fatalf("announced again after a restart: %+v", shown)
	}
	leads = leads[1:]
	w2.Check()
	leads = append(leads, Lead{Kind: "pending", ID: "a", About: "یک تصمیم"})
	w2.Check()
	if len(shown) != 3 || shown[2].URL != "daftar://go/home/pending/a" {
		t.Fatalf("back again: %+v", shown)
	}
}

func TestAFailedNoticeIsTriedAgain(t *testing.T) {
	var shown []Notice
	fail := true
	leads := []Lead{{Kind: "sync", About: ""}}
	w := watcher(t, &leads, &shown, &fail)
	w.Check()
	fail = false
	w.Check()
	if len(shown) != 1 || shown[0].URL != "daftar://go/home/sync" {
		t.Fatalf("%+v", shown)
	}
}

func TestABurstIsCapped(t *testing.T) {
	var leads []Lead
	for _, id := range []string{"a", "b", "c", "d", "e"} {
		leads = append(leads, Lead{Kind: "pending", ID: id, About: id})
	}
	n := Notices("home", "دفتر آنا", leads)
	if len(n) != burst || n[burst-1].URL != "daftar://go/home" || !strings.Contains(n[burst-1].Title, "3 مورد دیگر") {
		t.Fatalf("%+v", n)
	}
	if got := Notices("home", "x", leads[:burst]); len(got) != burst || got[burst-1].URL != "daftar://go/home/pending/c" {
		t.Fatalf("exactly a burst: %+v", got)
	}
}

func TestToastIsXMLWhateverTheGardenSays(t *testing.T) {
	n := Notice{Title: `دفتر <script>&"'`, Body: "</text></binding><actions><action content=\"x\" arguments=\"https://evil\"/>",
		Button: "باز کردن", URL: "daftar://go/home/pending/a"}
	var doc struct {
		Launch  string   `xml:"launch,attr"`
		Texts   []string `xml:"visual>binding>text"`
		Actions []struct {
			Arguments string `xml:"arguments,attr"`
		} `xml:"actions>action"`
	}
	if err := xml.Unmarshal([]byte(Toast(n)), &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Launch != n.URL || len(doc.Texts) != 2 || doc.Texts[0] != n.Title || doc.Texts[1] != n.Body ||
		len(doc.Actions) != 1 || doc.Actions[0].Arguments != n.URL {
		t.Fatalf("%+v", doc)
	}
}

// A LEAD NAMES WHOSE IT IS where the garden says (bin/leads.py): a case at a step, an open session.
func TestWhoseLead(t *testing.T) {
	n := Notices("home", "دفتر آنا", []Lead{{Kind: "case", ID: "repair", About: "repair waits at looked-at", For: "ben"},
		{Kind: "session", ID: "session-x", About: "an agent's session is open"}})
	if len(n) != 2 || !strings.Contains(n[0].Title, "ben") || n[0].URL != "daftar://go/home/case/repair" ||
		n[1].URL != "daftar://go/home/session/session-x" || strings.Contains(n[1].Title, "()") {
		t.Fatalf("whose a lead is, where the garden says: %+v", n)
	}
}

// A NOTICE SENT OFF THE MACHINE (design §8.2, a `send` under the flow row `sent-out`) carries the lead's sentence and
// its address, never what the lead is about: not the amount, not the name of the person it concerns.
func TestMailCarriesNoMaterial(t *testing.T) {
	leads := []Lead{{Kind: "pending", ID: "a", About: "the diagnosis of p-1a2b3c4d: 1500 USD"}, {Kind: "case", ID: "b", About: "x", For: "ben"}}
	msgs := MailNotices("home", "Ana's garden", leads)
	if len(msgs) != 2 {
		t.Fatalf("one mail a lead: %d", len(msgs))
	}
	m := string(Mail(msgs[0], "daftard <a@example.org>", "ana@example.org\r\nBcc: eve@example.org"))
	if strings.Contains(m, "diagnosis") || strings.Contains(m, "1500") || strings.Contains(m, "p-1a2b3c4d") {
		t.Fatalf("a mail carries no material: %s", m)
	}
	if !strings.Contains(m, "daftar://go/home/pending/a") || strings.Contains(m, "\nBcc:") || strings.Count(m, "\r\n\r\n") != 1 {
		t.Fatalf("the address, and no header broken into: %q", m)
	}
	if !strings.Contains(m, "Subject: =?UTF-8?B?") || !strings.Contains(m, "Content-Type: text/plain; charset=utf-8") {
		t.Fatalf("a subject in UTF-8, a body in plain text: %s", m)
	}
}
