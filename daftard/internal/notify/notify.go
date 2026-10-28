// Package notify tells a person, through their platform's own notifications, that something waits for their
// decision (design §2): one notice per new lead, naming whose garden it is, with one button that opens the lead's
// landing address (daftar://go/<garden>/<kind>/<id>). A notice carries no key and no decision: the page it opens reads
// the case from the garden, and the person decides there.
//
// On Windows a toast through the WinRT notification manager, raised by a PowerShell that shows no window, under
// daftard's own app id (registered with `daftard links`); its button is a protocol activation of the daftar: address.
// On Linux notify-send, whose "open" action opens the address. Elsewhere, nothing.
package notify

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

// AppID is daftard's app id for notifications (Windows: HKCU\Software\Classes\AppUserModelId\<AppID>).
const AppID = "Daftar.Hub"

// Opener opens a landing address where a notice's action comes back to daftard (Linux); daftard sets it to `open`.
// On Windows the toast's button is a protocol activation, and the system opens the address itself.
var Opener func(url string)

// QuietEnv is the switch that keeps a daftard's notices off the desktop of the machine it runs on: a daftard a test
// starts sets it (`DAFTARD_NOTIFY=off`), so a run leaves nothing on the desk; each notice is then a line of its log.
const QuietEnv = "DAFTARD_NOTIFY"

// Raise is how this daftard raises a notice: Show, or — with DAFTARD_NOTIFY=off — a line of its log, nothing shown.
func Raise(logf func(string, ...any)) func(Notice) error {
	if os.Getenv(QuietEnv) == "off" {
		return func(n Notice) error {
			if logf != nil {
				logf("notice, not raised (%s=off): %s — %s", QuietEnv, n.Title, n.Body)
			}
			return nil
		}
	}
	return Show
}

// A NOTICE LIVES AS LONG AS ITS DAFTARD: what still waits on the desktop when daftard stops is ended with it (Stop),
// and on Linux, where notify-send waits for the person, also when daftard dies without stopping (show_other.go).
var life, end = context.WithCancel(context.Background())

// Stop ends every notice still waiting, as daftard stops.
func Stop() { end() }

// restart gives notices a life again, after a Stop (a test's).
func restart() { life, end = context.WithCancel(context.Background()) }

// Notice is one notification.
type Notice struct {
	Title  string // whose garden, and what kind of thing waits
	Body   string // what it is, in the garden's own words
	Button string // the one action: open
	URL    string // the landing address it opens
}

// Lead is one thing waiting for a decision, as daftard's leads name it.
type Lead struct {
	Kind  string // pending, proposal, sync, case, session
	ID    string
	About string // its title, or whom it came from
	For   string // whose it is, where the garden says (bin/leads.py): a case's party; empty, the garden's gardener
}

func (l Lead) key() string { return l.Kind + "/" + l.ID }

// Watcher announces a garden's new leads, once each. What it announced is kept in the state folder, so a restart
// does not announce it again; a lead that went away and came back is announced again.
type Watcher struct {
	Garden string                 // the garden's name in landing addresses
	Whose  string                 // how its notices name it: «دفتر خانه»
	Path   string                 // the file it keeps what it announced in
	Show   func(Notice) error     // how a notice is raised (Show, or a test's)
	Leads  func() ([]Lead, error) // what waits now
	Log    func(string, ...any)   // daftard's log
	// Compose is how its notices are written: Notices on the machine; MailNotices off it, which carry no material.
	Compose func(garden, whose string, fresh []Lead) []Notice
	mu      sync.Mutex
}

// Group is a garden's watchers — on the machine, and each channel off it its flow law grants — checked together.
type Group []*Watcher

// Check checks each watcher of the group.
func (g Group) Check() {
	for _, w := range g {
		w.Check()
	}
}

// At most this many notices at once; the rest are one notice that opens the garden's list.
const burst = 3

var kinds = map[string]string{"pending": "تصمیمی منتظر شماست", "proposal": "پیشنهادی از دفتری دیگر", "sync": "همگام‌سازی نیاز به بررسی دارد",
	"case": "پرونده‌ای در مرحله‌ای منتظر است", "session": "کار نشستی باز مانده است",
	"health": "خرابی‌ای که خوانده شده و هنوز درست نشده", "obligation": "تعهدی که موعدش نزدیک است", "form": "پاسخ‌های فرمی منتظر گرفته شدن",
	"action": "اقدامی منتظر تأیید شما", "passkey": "کلیدی برای ورود، منتظر ثبت به نام صاحبش"}

// Check reads what waits and announces what is new since the last check.
func (w *Watcher) Check() {
	w.mu.Lock()
	defer w.mu.Unlock()
	leads, err := w.Leads()
	if err != nil {
		w.log("leads: %v", err)
		return
	}
	seen := map[string]bool{}
	if b, err := os.ReadFile(w.Path); err == nil {
		var keys []string
		if json.Unmarshal(b, &keys) == nil {
			for _, k := range keys {
				seen[k] = true
			}
		}
	}
	var fresh []Lead
	now := []string{}
	for _, l := range leads {
		now = append(now, l.key())
		if !seen[l.key()] {
			fresh = append(fresh, l)
		}
	}
	compose := w.Compose
	if compose == nil {
		compose = Notices
	}
	for i, n := range compose(w.Garden, w.Whose, fresh) {
		if err := w.Show(n); err != nil {
			w.log("notice %d: %v", i, err)
			return // not kept as announced: the next check tries again
		}
	}
	sort.Strings(now)
	b, _ := json.Marshal(now)
	if err := os.MkdirAll(filepath.Dir(w.Path), 0o700); err == nil {
		_ = os.WriteFile(w.Path, b, 0o600)
	}
	if len(fresh) > 0 {
		w.log("announced %d new lead(s)", len(fresh))
	}
}

func (w *Watcher) log(f string, a ...any) {
	if w.Log != nil {
		w.Log("["+w.Garden+"] notify: "+f, a...)
	}
}

// Notices are what announces `fresh`: one each, or, past the burst, the first ones and one for the rest.
func Notices(garden, whose string, fresh []Lead) []Notice {
	addr := func(l Lead) string {
		u := "daftar://go/" + garden + "/" + l.Kind
		if l.ID != "" {
			u += "/" + l.ID
		}
		return u
	}
	var out []Notice
	for i, l := range fresh {
		if len(fresh) > burst && i == burst-1 {
			out = append(out, Notice{Title: whose + " — " + fmt.Sprint(len(fresh)-i) + " مورد دیگر منتظر شماست",
				Body: "فهرست همهٔ آن‌ها را باز کنید.", Button: "باز کردن", URL: "daftar://go/" + garden})
			break
		}
		what := kinds[l.Kind]
		if what == "" {
			what = "موردی منتظر شماست"
		}
		if l.For != "" {
			what += " (" + l.For + ")" // whose it is, as the garden names them
		}
		out = append(out, Notice{Title: whose + " — " + what, Body: strings.TrimSpace(l.About), Button: "باز کردن", URL: addr(l)})
	}
	return out
}

func esc(s string) string {
	var b strings.Builder
	_ = xml.EscapeText(&b, []byte(s))
	return b.String()
}

// Toast is a notice as a Windows toast's XML: every value escaped, the address a protocol activation.
func Toast(n Notice) string {
	return `<toast activationType="protocol" launch="` + esc(n.URL) + `"><visual><binding template="ToastGeneric"><text>` +
		esc(n.Title) + `</text><text>` + esc(n.Body) + `</text></binding></visual><actions><action content="` + esc(n.Button) +
		`" activationType="protocol" arguments="` + esc(n.URL) + `"/></actions></toast>`
}

// MailNotices are what announces `fresh` off the machine (design §8.2): the lead's sentence and its address alone. What
// the lead is about stays in the garden, read on the page: a mail that left the machine would carry it everywhere a mail
// goes.
func MailNotices(garden, whose string, fresh []Lead) []Notice {
	out := Notices(garden, whose, fresh)
	for i := range out {
		out[i].Body = "باز کردن روی رایانهٔ خودتان — Open it on your own machine: " + out[i].URL
	}
	return out
}

func oneLine(s string) string { return strings.Join(strings.Fields(s), " ") }

// Mail is a notice as a message for sendmail (-t): its headers on one line each, the subject in UTF-8, the body text.
func Mail(n Notice, from, to string) []byte {
	subject := "=?UTF-8?B?" + base64.StdEncoding.EncodeToString([]byte(oneLine(n.Title))) + "?="
	var b strings.Builder
	b.WriteString("From: " + oneLine(from) + "\r\n")
	b.WriteString("To: " + oneLine(to) + "\r\n")
	b.WriteString("Subject: " + subject + "\r\n")
	b.WriteString("MIME-Version: 1.0\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: 8bit\r\n\r\n")
	b.WriteString(strings.ReplaceAll(strings.ReplaceAll(n.Body, "\r\n", "\n"), "\n", "\r\n") + "\r\n")
	return []byte(b.String())
}
