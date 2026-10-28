package main

// How this account's daftard is started and kept running, on the two systems whose service managers `daftard install`
// writes for besides Windows' logon task (installWindows): on Linux a systemd user unit, on macOS a launchd agent. Each
// runs `daftard serve`, which starts one daemon for each garden and, where a garden says `routines: true`, asks its
// bin/routines.py tick each minute. So no routine needs a cron line or a launchd job of its own: daftard is the one job
// the system keeps, and the clock of every routine. A routine a crontab or a launchd job still runs is that register's
// (`be … as: presence` on its walk), and daftard's tick leaves it alone; both at once is a refusal, never two runs.

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/0mit/daftar/daftard/internal/proc"
)

// launchdLabel is daftard's job in launchd's domain of this user.
const launchdLabel = "daftar.daftard"

// carried is what the service runs daftard with from the account that installed it: the state folder where one is
// named (a second daftard beside the first), and the PATH, since a service manager's own reaches neither Homebrew's
// git nor a Python in the account's folder.
func carried() [][2]string {
	var env [][2]string
	if v := os.Getenv("DAFTARD_STATE"); v != "" {
		env = append(env, [2]string{"DAFTARD_STATE", v})
	}
	if v := os.Getenv("PATH"); v != "" {
		env = append(env, [2]string{"PATH", v})
	}
	return env
}

// systemdQuote is a word of a unit file as systemd reads it: in double quotes, its backslash and quote escaped, and
// a percent sign doubled (a specifier otherwise).
func systemdQuote(s string) string {
	s = strings.NewReplacer(`\`, `\\`, `"`, `\"`, "%", "%%").Replace(s)
	return `"` + s + `"`
}

// unitText is the systemd user unit that keeps daftard running for this account.
func unitText(exe string, env [][2]string) string {
	var b strings.Builder
	b.WriteString("[Unit]\nDescription=daftard: this account's gardens, their pages, their sync and their routines\n\n")
	b.WriteString("[Service]\nExecStart=" + systemdQuote(exe) + " serve\n")
	for _, e := range env {
		b.WriteString("Environment=" + systemdQuote(e[0]+"="+e[1]) + "\n")
	}
	b.WriteString("Restart=on-failure\nRestartSec=10\n\n[Install]\nWantedBy=default.target\n")
	return b.String()
}

// xmlEscape is a string of a property list.
func xmlEscape(s string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;", "'", "&apos;").Replace(s)
}

// plistText is the launchd agent that keeps daftard running for this user: started at login and when loaded, and
// started again whenever it ends other than by `daftard stop`.
func plistText(exe string, env [][2]string) string {
	var b strings.Builder
	b.WriteString(`<?xml version="1.0" encoding="UTF-8"?>` + "\n" +
		`<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">` + "\n" +
		`<plist version="1.0">` + "\n<dict>\n")
	b.WriteString("\t<key>Label</key>\n\t<string>" + launchdLabel + "</string>\n")
	b.WriteString("\t<key>ProgramArguments</key>\n\t<array>\n\t\t<string>" + xmlEscape(exe) + "</string>\n\t\t<string>serve</string>\n\t</array>\n")
	if len(env) > 0 {
		b.WriteString("\t<key>EnvironmentVariables</key>\n\t<dict>\n")
		for _, e := range env {
			b.WriteString("\t\t<key>" + xmlEscape(e[0]) + "</key>\n\t\t<string>" + xmlEscape(e[1]) + "</string>\n")
		}
		b.WriteString("\t</dict>\n")
	}
	b.WriteString("\t<key>RunAtLoad</key>\n\t<true/>\n")
	b.WriteString("\t<key>KeepAlive</key>\n\t<dict>\n\t\t<key>SuccessfulExit</key>\n\t\t<false/>\n\t</dict>\n")
	b.WriteString("\t<key>ProcessType</key>\n\t<string>Background</string>\n</dict>\n</plist>\n")
	return b.String()
}

// unitPath is where systemd reads this user's units.
func unitPath() string {
	base := os.Getenv("XDG_CONFIG_HOME")
	if base == "" {
		base = filepath.Join(os.Getenv("HOME"), ".config")
	}
	return filepath.Join(base, "systemd", "user", "daftard.service")
}

// agentPath is where launchd reads this user's agents.
func agentPath() string {
	return filepath.Join(os.Getenv("HOME"), "Library", "LaunchAgents", launchdLabel+".plist")
}

// writeService writes a service's file, saying whether it changed.
func writeService(path, text string) (bool, error) {
	if old, err := os.ReadFile(path); err == nil && string(old) == text {
		return false, nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return false, err
	}
	return true, os.WriteFile(path, []byte(text), 0o644)
}

// said runs a service manager's command and gives what it said, trimmed.
func said(name string, args ...string) (string, error) {
	out, err := proc.Command(name, args...).CombinedOutput()
	return strings.TrimSpace(string(out)), err
}

// installSystemd writes the user unit and has systemd run it now and at each start. Where this account has no systemd
// of its own to ask (a container, a session with no user bus), it says so and how daftard is started instead; it is
// never an error, as links are not on a machine with no desktop.
func installSystemd() {
	self, err := os.Executable()
	if err != nil {
		fmt.Println("daftar: no service written:", err)
		return
	}
	path := unitPath()
	if _, err := writeService(path, unitText(self, carried())); err != nil {
		fmt.Println("daftar: the systemd unit was not written:", err)
		return
	}
	fmt.Println("wrote", path)
	if _, err := exec.LookPath("systemctl"); err != nil {
		fmt.Println("daftar: this machine has no systemctl: start daftard with `daftard serve`, by whatever starts this account's programs")
		return
	}
	for _, a := range [][]string{{"--user", "daemon-reload"}, {"--user", "enable", "daftard.service"}, {"--user", "restart", "daftard.service"}} {
		if out, err := said("systemctl", a...); err != nil {
			fmt.Printf("daftar: `systemctl %s` did not run (%s): start daftard with `daftard serve`\n", strings.Join(a, " "), firstLine(out, err))
			return
		}
	}
	fmt.Println("installed: the systemd user unit daftard.service, enabled and started")
	if out, err := said("loginctl", "show-user", strconv.Itoa(os.Getuid()), "--property=Linger", "--value"); err == nil && out == "no" {
		fmt.Println("daftar: systemd runs it while this account is logged in; to tick routines with nobody logged in: " +
			"`loginctl enable-linger`")
	}
}

// installLaunchd writes the user agent and loads it into this user's domain: the login session's where there is one,
// else the user's background domain (a session over ssh).
func installLaunchd() {
	self, err := os.Executable()
	if err != nil {
		fmt.Println("daftar: no service written:", err)
		return
	}
	path := agentPath()
	if _, err := writeService(path, plistText(self, carried())); err != nil {
		fmt.Println("daftar: the launchd agent was not written:", err)
		return
	}
	fmt.Println("wrote", path)
	uid := strconv.Itoa(os.Getuid())
	var last string
	for _, domain := range []string{"gui/" + uid, "user/" + uid} {
		_, _ = said("launchctl", "bootout", domain+"/"+launchdLabel) // the one loaded before, if any, with the binary it ran
		out, err := said("launchctl", "bootstrap", domain, path)
		if err == nil {
			fmt.Printf("installed: the launchd agent %s, loaded in %s and started\n", launchdLabel, domain)
			return
		}
		last = firstLine(out, err)
	}
	fmt.Printf("daftar: launchctl did not load it (%s): start daftard with `daftard serve`\n", last)
}

func firstLine(out string, err error) string {
	if out == "" {
		return err.Error()
	}
	return strings.SplitN(out, "\n", 2)[0]
}
