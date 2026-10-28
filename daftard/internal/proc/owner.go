package proc

import (
	"encoding/hex"
	"net"
	"os"
	"runtime"
	"strconv"
	"strings"
)

// ListenerUIDs are the accounts (uids) of the listening TCP sockets a connection to addr (host:port) would reach: its
// own address or the unspecified one, at its port. On Linux they are read from /proc/net/tcp and tcp6, which name
// every socket's owner; elsewhere, and where those cannot be read, none — the caller cannot tell, and says so itself.
// `localhost` is 127.0.0.1 and ::1.
func ListenerUIDs(addr string) []int {
	if runtime.GOOS != "linux" {
		return nil
	}
	host, port, err := net.SplitHostPort(addr)
	if err != nil {
		return nil
	}
	p, err := strconv.Atoi(port)
	if err != nil {
		return nil
	}
	var targets []net.IP
	if host == "localhost" {
		targets = []net.IP{net.IPv4(127, 0, 0, 1), net.IPv6loopback}
	} else if ip := net.ParseIP(host); ip != nil {
		targets = []net.IP{ip}
	} else {
		return nil
	}
	var out []int
	for _, f := range []string{"/proc/net/tcp", "/proc/net/tcp6"} {
		if b, err := os.ReadFile(f); err == nil {
			out = append(out, listenersAt(string(b), targets, p)...)
		}
	}
	return out
}

// listenersAt reads one /proc/net/tcp{,6} table: the uid of each socket listening (state 0A) at port on one of the
// targets, or on the unspecified address, which takes them all.
func listenersAt(table string, targets []net.IP, port int) []int {
	var out []int
	for _, line := range strings.Split(table, "\n") {
		f := strings.Fields(line)
		if len(f) < 8 || f[3] != "0A" {
			continue
		}
		a, pt, ok := strings.Cut(f[1], ":")
		if !ok {
			continue
		}
		if n, err := strconv.ParseUint(pt, 16, 16); err != nil || int(n) != port {
			continue
		}
		ip := kernelIP(a)
		if ip == nil {
			continue
		}
		hit := ip.IsUnspecified()
		for _, t := range targets {
			hit = hit || ip.Equal(t)
		}
		if !hit {
			continue
		}
		if uid, err := strconv.Atoi(f[7]); err == nil {
			out = append(out, uid)
		}
	}
	return out
}

// kernelIP reads an address as the kernel writes it in /proc/net/tcp: 8 or 32 hex digits, each 32-bit word in the
// machine's own byte order (little-endian on the machines daftard runs on).
func kernelIP(s string) net.IP {
	b, err := hex.DecodeString(s)
	if err != nil || (len(b) != 4 && len(b) != 16) {
		return nil
	}
	for i := 0; i < len(b); i += 4 {
		b[i], b[i+1], b[i+2], b[i+3] = b[i+3], b[i+2], b[i+1], b[i]
	}
	return net.IP(b)
}
