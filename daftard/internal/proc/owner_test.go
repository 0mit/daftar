package proc

import (
	"net"
	"os"
	"reflect"
	"runtime"
	"testing"
)

// A /proc/net/tcp table as the kernel writes it: who listens where.
const tcp4 = `  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 0100007F:2292 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1001        0 6848843 1
   1: 00000000:2293 00000000:0000 0A 00000000:00000000 00:00000000 00000000    99        0 2568242 1
   2: 0100007F:2292 0100007F:D49B 01 00000000:00000000 00:00000000 00000000  1002        0 2568243 1
   3: 7B00A8C0:2294 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1003        0 2568244 1
   4: 0100007F:2295 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1004        0 2568245 1
`
const tcp6 = `  sl  local_address                         remote_address                        st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 00000000000000000000000001000000:2292 00000000000000000000000000000000:0000 0A 00000000:00000000 00:00000000 00000000  1005        0 7088658 1
   1: 0000000000000000FFFF00000100007F:2296 00000000000000000000000000000000:0000 0A 00000000:00000000 00:00000000 00000000  1006        0 24348 1
   2: 00000000000000000000000000000000:2293 00000000000000000000000000000000:0000 0A 00000000:00000000 00:00000000 00000000  1007        0 24349 1
`

// WHO LISTENS AT AN ADDRESS: the listening sockets a connection there would reach — its own address, or the one that
// takes them all — and nothing connected, nothing at another address or port.
func TestListenersAt(t *testing.T) {
	lo4, lo6 := []net.IP{net.IPv4(127, 0, 0, 1)}, []net.IP{net.IPv6loopback}
	for _, c := range []struct {
		table   string
		targets []net.IP
		port    int
		want    []int
	}{
		{tcp4, lo4, 0x2292, []int{1001}},                 // 127.0.0.1:8850, listening (the connected one is not)
		{tcp4, lo4, 0x2293, []int{99}},                   // 0.0.0.0 takes 127.0.0.1 too
		{tcp4, lo4, 0x2294, nil},                         // another address, its own port
		{tcp4, lo4, 0x2299, nil},                         // nobody there
		{tcp6, lo6, 0x2292, []int{1005}},                 // ::1
		{tcp6, lo4, 0x2296, []int{1006}},                 // ::ffff:127.0.0.1
		{tcp6, lo4, 0x2293, []int{1007}},                 // :: takes them all
		{tcp6, append(lo4, lo6...), 0x2292, []int{1005}}, // localhost: both
	} {
		if got := listenersAt(c.table, c.targets, c.port); !reflect.DeepEqual(got, c.want) {
			t.Errorf("port %x at %v: %v, want %v", c.port, c.targets, got, c.want)
		}
	}
}

// On this machine, a socket this test listens on is read as this account's.
func TestListenerUIDsHere(t *testing.T) {
	if runtime.GOOS != "linux" {
		if ListenerUIDs("127.0.0.1:1") != nil {
			t.Fatal("elsewhere than Linux nothing can be told")
		}
		return
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()
	got := ListenerUIDs(ln.Addr().String())
	if len(got) != 1 || got[0] != os.Getuid() {
		t.Fatalf("this test's own listener is read as this account's (%d): %v", os.Getuid(), got)
	}
	_, port, _ := net.SplitHostPort(ln.Addr().String())
	if got := ListenerUIDs("localhost:" + port); len(got) != 1 || got[0] != os.Getuid() {
		t.Fatalf("localhost is the loopback: %v", got)
	}
}
