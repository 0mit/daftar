package passkey

import (
	"crypto"
	"crypto/ecdsa"
	"crypto/ed25519"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"strings"
	"testing"
)

// a CBOR writer for the authenticator this test plays: maps with integer or text keys, byte and text strings,
// integers
func enc(v any) []byte {
	head := func(major byte, n uint64) []byte {
		switch {
		case n < 24:
			return []byte{major<<5 | byte(n)}
		case n < 256:
			return []byte{major<<5 | 24, byte(n)}
		case n < 65536:
			return []byte{major<<5 | 25, byte(n >> 8), byte(n)}
		}
		b := make([]byte, 5)
		b[0] = major<<5 | 26
		binary.BigEndian.PutUint32(b[1:], uint32(n))
		return b
	}
	switch x := v.(type) {
	case int:
		if x >= 0 {
			return head(0, uint64(x))
		}
		return head(1, uint64(-1-x))
	case []byte:
		return append(head(2, uint64(len(x))), x...)
	case string:
		return append(head(3, uint64(len(x))), x...)
	case [][2]any: // a map in the order given
		out := head(5, uint64(len(x)))
		for _, kv := range x {
			out = append(append(out, enc(kv[0])...), enc(kv[1])...)
		}
		return out
	}
	panic("enc")
}

type device struct {
	alg  int
	sign func(data []byte) []byte
	cose []byte
	id   []byte
}

func newDevice(t *testing.T, alg int) *device {
	id := make([]byte, 32)
	_, _ = rand.Read(id)
	d := &device{alg: alg, id: id}
	switch alg {
	case -7:
		k, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
		x, y := make([]byte, 32), make([]byte, 32)
		k.X.FillBytes(x)
		k.Y.FillBytes(y)
		d.cose = enc([][2]any{{1, 2}, {3, -7}, {-1, 1}, {-2, x}, {-3, y}})
		d.sign = func(data []byte) []byte {
			h := sha256.Sum256(data)
			s, _ := ecdsa.SignASN1(rand.Reader, k, h[:])
			return s
		}
	case -8:
		pub, priv, _ := ed25519.GenerateKey(rand.Reader)
		d.cose = enc([][2]any{{1, 1}, {3, -8}, {-1, 6}, {-2, []byte(pub)}})
		d.sign = func(data []byte) []byte { return ed25519.Sign(priv, data) }
	case -257:
		k, _ := rsa.GenerateKey(rand.Reader, 2048)
		d.cose = enc([][2]any{{1, 3}, {3, -257}, {-1, k.N.Bytes()}, {-2, []byte{1, 0, 1}}})
		d.sign = func(data []byte) []byte {
			h := sha256.Sum256(data)
			s, _ := rsa.SignPKCS1v15(rand.Reader, k, crypto.SHA256, h[:])
			return s
		}
	}
	return d
}

func client(typ string, challenge []byte, origin string) []byte {
	b, _ := json.Marshal(map[string]any{"type": typ, "challenge": b64.EncodeToString(challenge), "origin": origin, "crossOrigin": false})
	return b
}

func auth(rpID string, flags byte, credID, cose []byte) []byte {
	h := sha256.Sum256([]byte(rpID))
	out := append(h[:], flags, 0, 0, 0, 7)
	if credID != nil {
		out = append(out, make([]byte, 16)...)
		out = append(out, byte(len(credID)>>8), byte(len(credID)))
		out = append(append(out, credID...), cose...)
	}
	return out
}

const origin, rp = "https://daftar.example.org", "daftar.example.org"

// A PASSKEY REGISTERED, THEN SIGNED IN WITH — for each of the three algorithms a page asks for — and every way a
// sign-in may be false refused: another challenge, another origin, another site, nobody present, the wrong ceremony,
// a credential the garden does not name, a key that is not its own, a signature changed.
func TestRegisterAndSignIn(t *testing.T) {
	for _, alg := range Algorithms {
		d := newDevice(t, alg)
		ch := []byte("a-challenge-of-thirty-two-bytes!")
		att := enc([][2]any{{"fmt", "none"}, {"attStmt", [][2]any{}}, {"authData", auth(rp, flagUP|flagUV|flagAT, d.id, d.cose)}})
		anchor, err := Register(client("webauthn.create", ch, origin), att, ch, origin, rp)
		if err != nil {
			t.Fatalf("alg %d: registered: %v", alg, err)
		}
		if !strings.HasPrefix(anchor, b64.EncodeToString(d.id)+".") {
			t.Fatalf("alg %d: the anchor is the credential id and its key: %s", alg, anchor)
		}
		if _, _, err := ParseAnchor(anchor); err != nil {
			t.Fatalf("alg %d: the anchor reads back: %v", alg, err)
		}
		if _, err := Register(client("webauthn.create", ch, origin), att, []byte("another challenge, not this one!"), origin, rp); err == nil {
			t.Fatalf("alg %d: a registration answering another challenge is refused", alg)
		}
		other := newDevice(t, -7)
		otherAnchor := Anchor(d.id, other.cose) // the same id, a key that is not this device's
		ch2 := []byte("the-sign-in-challenge-32-bytes!!")
		cd := client("webauthn.get", ch2, origin)
		ad := auth(rp, flagUP|flagUV, nil, nil)
		h := sha256.Sum256(cd)
		sig := d.sign(append(append([]byte(nil), ad...), h[:]...))
		if got, n, err := SignIn(d.id, cd, ad, sig, ch2, origin, rp, []string{"junk", anchor}); err != nil || got != anchor || n != 7 {
			t.Fatalf("alg %d: signed in by the key the garden names, its counter read (%d): %v", alg, n, err)
		}
		presence := auth(rp, flagUP, nil, nil) // a touch, no PIN or face
		presenceSig := d.sign(append(append([]byte(nil), presence...), h[:]...))
		bad := map[string]func() error{
			"presence without verification": func() error {
				_, _, e := SignIn(d.id, cd, presence, presenceSig, ch2, origin, rp, []string{anchor})
				return e
			},
			"another challenge": func() error {
				_, _, e := SignIn(d.id, cd, ad, sig, []byte("x"), origin, rp, []string{anchor})
				return e
			},
			"another origin": func() error {
				_, _, e := SignIn(d.id, cd, ad, sig, ch2, "https://evil.example", rp, []string{anchor})
				return e
			},
			"another site": func() error {
				_, _, e := SignIn(d.id, cd, ad, sig, ch2, origin, "evil.example", []string{anchor})
				return e
			},
			"nobody present": func() error {
				ad0 := auth(rp, 0, nil, nil)
				s0 := d.sign(append(append([]byte(nil), ad0...), h[:]...))
				_, _, e := SignIn(d.id, cd, ad0, s0, ch2, origin, rp, []string{anchor})
				return e
			},
			"the registering ceremony": func() error {
				cc := client("webauthn.create", ch2, origin)
				_, _, e := SignIn(d.id, cc, ad, sig, ch2, origin, rp, []string{anchor})
				return e
			},
			"a credential not named": func() error {
				_, _, e := SignIn([]byte("someone else's credential"), cd, ad, sig, ch2, origin, rp, []string{anchor})
				return e
			},
			"a key not its own": func() error {
				_, _, e := SignIn(d.id, cd, ad, sig, ch2, origin, rp, []string{otherAnchor})
				return e
			},
			"a signature changed": func() error {
				s := append([]byte(nil), sig...)
				s[len(s)-1] ^= 1
				_, _, e := SignIn(d.id, cd, ad, s, ch2, origin, rp, []string{anchor})
				return e
			},
		}
		for name, try := range bad {
			if try() == nil {
				t.Fatalf("alg %d: %s is refused", alg, name)
			}
		}
	}
}

func TestCBORRefusesWhatItDoesNotTake(t *testing.T) {
	for name, b := range map[string][]byte{
		"cut short":         {0x5f},
		"indefinite length": {0x9f, 0x01, 0xff},
		"a float":           {0xfb, 0, 0, 0, 0, 0, 0, 0, 0},
		"a string too long": {0x58, 0xff, 1, 2},
		"a huge array":      {0x9b, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
	} {
		if _, _, err := cbor(b, 0); err == nil {
			t.Fatalf("%s is refused", name)
		}
	}
	deep := make([]byte, 40)
	for i := range deep {
		deep[i] = 0x81
	}
	if _, _, err := cbor(deep, 0); err == nil {
		t.Fatalf("nesting too deep is refused")
	}
}
