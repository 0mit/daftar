#!/usr/bin/env python3
"""view_fetch — what a monitor's adapter reads over the network, bounded (security audit 2026-10-10, 3.6).

A served page asks its monitors for values on every viewer's poll, so a monitor that answers slowly, at length or by
sending the host elsewhere would hold the host's threads and memory, or turn its reads toward another address. Each
read here is therefore:
  - ONE DEADLINE for the whole answer — connecting, the headers and the body — not a timeout per read of the socket:
    an answer dripped a byte at a time costs the deadline, and then the connection is cut;
  - CAPPED in size (4 MiB by default): an answer larger than any page needs is refused, not read whole;
  - READ WHERE IT WAS ASKED: an answer that sends the host elsewhere (a redirect) is refused and never followed;
  - TAKEN AS AN ANSWER only with status 200.
A monitor is read directly, as its host's configuration gives its address — never through a proxy the environment
names — since a monitor is local and unauthenticated (README, "Live values").
"""
import http.client, json, socket, threading, time, urllib.parse

DEADLINE = 5.0          # seconds for one whole answer
MAX_BYTES = 4 << 20     # the largest answer read


class Refused(Exception):
    """A monitor's answer the host does not take: late, too large, elsewhere, or not an answer."""


def get_json(url, deadline=DEADLINE, cap=MAX_BYTES):
    """The JSON document at `url`, read within `deadline` seconds and `cap` bytes, or Refused."""
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise Refused("a monitor is read over http or https, at an address with a host: %r is not one" % url)
    conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(
        u.hostname, u.port, timeout=max(0.1, deadline))
    cut, held = threading.Event(), {}

    def cut_off():                       # the deadline: whatever the read is waiting on ends now
        cut.set()
        s = held.get("sock") or conn.sock   # an answer that closes its connection takes the socket from `conn`
        if s is not None:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
    timer = threading.Timer(deadline, cut_off)
    timer.daemon = True
    timer.start()
    try:
        conn.request("GET", (u.path or "/") + ("?" + u.query if u.query else ""), headers={"Accept": "application/json"})
        held["sock"] = conn.sock
        r = conn.getresponse()
        if r.status != 200:
            raise Refused("the monitor answered %d%s" % (r.status, " (a redirect is not followed)" if 300 <= r.status < 400 else ""))
        n = r.getheader("Content-Length")
        if n and n.isdigit() and int(n) > cap:
            raise Refused("the monitor's answer is %s bytes, past the %d read" % (n, cap))
        body = bytearray()
        while True:
            chunk = r.read1(65536)
            if not chunk:
                break
            body += chunk
            if len(body) > cap:
                raise Refused("the monitor's answer is past the %d bytes read" % cap)
        if cut.is_set():
            raise Refused("the monitor's answer took longer than %s s" % deadline)
        return json.loads(body)
    except (OSError, http.client.HTTPException) as e:
        raise Refused("the monitor's answer took longer than %s s" % deadline if cut.is_set() else "the monitor: %s" % e)
    finally:
        timer.cancel()
        conn.close()


class Budget:
    """One poll's time, shared by the reads it makes: each read gets the deadline or what is left of the poll's time,
    whichever is less, and none once it is spent — a slow monitor costs one poll its budget, never a deadline a value."""

    def __init__(self, seconds):
        self.until = time.monotonic() + seconds

    def left(self, most=DEADLINE):
        return max(0.0, min(most, self.until - time.monotonic()))
