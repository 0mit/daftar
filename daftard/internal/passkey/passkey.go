// Package passkey verifies a person's passkey (W3C Web Authentication, level 2): registering one, and signing in with
// it. It reads what a browser's authenticator gives — CBOR, a COSE public key, authenticator data — with the standard
// library alone, and keeps nothing: the key a person registered is named in their own bean (the namespace `passkey`:
// its credential id and its COSE public key, base64url, joined by a dot), added by the gardener (class F), and a sign-in
// is verified against what the garden says.
//
// Attestation is not asked for ("none"): who made the authenticator is not what is proved; that this person holds
// the key the gardener named is.
package passkey

import (
	"bytes"
	"crypto"
	"crypto/ecdsa"
	"crypto/ed25519"
	"crypto/elliptic"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"strings"
)

// The COSE algorithms a page asks for, in its order of preference: ES256, EdDSA, RS256.
var Algorithms = []int{-7, -8, -257}

// Flags of the authenticator data.
const (
	flagUP = 0x01 // the user was present
	flagUV = 0x04 // the user was verified
	flagAT = 0x40 // attested credential data follows
)

var b64 = base64.RawURLEncoding

// ------------------------------------------------------------------------------------------------ CBOR (RFC 8949)

// cbor reads one data item: a map is map[any]any (keys int64 or string), an array []any, a byte string []byte, a
// text string string, an integer int64, and true, false and null. It returns the item and the bytes it took.
func cbor(b []byte, depth int) (any, int, error) {
	if depth > 16 {
		return nil, 0, errors.New("cbor: nested too deep")
	}
	if len(b) == 0 {
		return nil, 0, errors.New("cbor: ends early")
	}
	major, info := b[0]>>5, b[0]&0x1f
	n, used, err := argument(b, info)
	if err != nil {
		return nil, 0, err
	}
	switch major {
	case 0:
		if n > 1<<62 {
			return nil, 0, errors.New("cbor: integer too large")
		}
		return int64(n), used, nil
	case 1:
		if n > 1<<62 {
			return nil, 0, errors.New("cbor: integer too large")
		}
		return -1 - int64(n), used, nil
	case 2, 3:
		if n > uint64(len(b)-used) {
			return nil, 0, errors.New("cbor: string runs past the end")
		}
		s := b[used : used+int(n)]
		if major == 2 {
			return append([]byte(nil), s...), used + int(n), nil
		}
		return string(s), used + int(n), nil
	case 4:
		if n > uint64(len(b)) {
			return nil, 0, errors.New("cbor: array longer than its bytes")
		}
		out := make([]any, 0, n)
		for i := uint64(0); i < n; i++ {
			v, k, err := cbor(b[used:], depth+1)
			if err != nil {
				return nil, 0, err
			}
			out, used = append(out, v), used+k
		}
		return out, used, nil
	case 5:
		if n > uint64(len(b)) {
			return nil, 0, errors.New("cbor: map longer than its bytes")
		}
		out := make(map[any]any, n)
		for i := uint64(0); i < n; i++ {
			k, ku, err := cbor(b[used:], depth+1)
			if err != nil {
				return nil, 0, err
			}
			used += ku
			v, vu, err := cbor(b[used:], depth+1)
			if err != nil {
				return nil, 0, err
			}
			used += vu
			switch k.(type) {
			case int64, string:
				out[k] = v
			default:
				return nil, 0, errors.New("cbor: a map key that is neither integer nor text")
			}
		}
		return out, used, nil
	case 7:
		switch info {
		case 20:
			return false, 1, nil
		case 21:
			return true, 1, nil
		case 22:
			return nil, 1, nil
		}
	}
	return nil, 0, fmt.Errorf("cbor: an item this reader does not take (major %d, info %d)", major, info)
}

func argument(b []byte, info byte) (uint64, int, error) {
	switch {
	case info < 24:
		return uint64(info), 1, nil
	case info == 24 && len(b) >= 2:
		return uint64(b[1]), 2, nil
	case info == 25 && len(b) >= 3:
		return uint64(binary.BigEndian.Uint16(b[1:3])), 3, nil
	case info == 26 && len(b) >= 5:
		return uint64(binary.BigEndian.Uint32(b[1:5])), 5, nil
	case info == 27 && len(b) >= 9:
		return binary.BigEndian.Uint64(b[1:9]), 9, nil
	}
	return 0, 0, errors.New("cbor: an argument this reader does not take (indefinite length, or cut short)")
}

// ------------------------------------------------------------------------------------------------ COSE keys (RFC 9053)

// Key is a passkey's public key, as its COSE key says it.
type Key struct {
	Alg int
	Pub crypto.PublicKey
}

func intOf(m map[any]any, k int64) (int64, bool) {
	v, ok := m[k].(int64)
	return v, ok
}

func bytesOf(m map[any]any, k int64) []byte {
	v, _ := m[k].([]byte)
	return v
}

// ParseKey reads a COSE public key: EC2 on P-256 for ES256, OKP Ed25519 for EdDSA, RSA for RS256.
func ParseKey(cose []byte) (*Key, error) {
	v, n, err := cbor(cose, 0)
	if err != nil {
		return nil, err
	}
	if n != len(cose) {
		return nil, errors.New("cose: bytes after the key")
	}
	m, ok := v.(map[any]any)
	if !ok {
		return nil, errors.New("cose: not a map")
	}
	kty, _ := intOf(m, 1)
	alg, _ := intOf(m, 3)
	switch {
	case kty == 2 && alg == -7:
		crv, _ := intOf(m, -1)
		x, y := bytesOf(m, -2), bytesOf(m, -3)
		if crv != 1 || len(x) != 32 || len(y) != 32 {
			return nil, errors.New("cose: an ES256 key is on P-256, x and y 32 bytes each")
		}
		pub := &ecdsa.PublicKey{Curve: elliptic.P256(), X: new(big.Int).SetBytes(x), Y: new(big.Int).SetBytes(y)}
		if !pub.Curve.IsOnCurve(pub.X, pub.Y) {
			return nil, errors.New("cose: the point is not on P-256")
		}
		return &Key{Alg: -7, Pub: pub}, nil
	case kty == 1 && alg == -8:
		crv, _ := intOf(m, -1)
		x := bytesOf(m, -2)
		if crv != 6 || len(x) != ed25519.PublicKeySize {
			return nil, errors.New("cose: an EdDSA key is Ed25519, x 32 bytes")
		}
		return &Key{Alg: -8, Pub: ed25519.PublicKey(x)}, nil
	case kty == 3 && alg == -257:
		nb, eb := bytesOf(m, -1), bytesOf(m, -2)
		if len(nb) < 256 || len(eb) == 0 || len(eb) > 8 {
			return nil, errors.New("cose: an RS256 key has a modulus of 2048 bits or more")
		}
		e := new(big.Int).SetBytes(eb)
		if !e.IsInt64() || e.Int64() < 3 {
			return nil, errors.New("cose: an RSA exponent this reader does not take")
		}
		return &Key{Alg: -257, Pub: &rsa.PublicKey{N: new(big.Int).SetBytes(nb), E: int(e.Int64())}}, nil
	}
	return nil, fmt.Errorf("cose: a key this reader does not take (kty %d, alg %d)", kty, alg)
}

// Verify checks a signature over data with the key.
func (k *Key) Verify(data, sig []byte) bool {
	switch pub := k.Pub.(type) {
	case *ecdsa.PublicKey:
		d := sha256.Sum256(data)
		return ecdsa.VerifyASN1(pub, d[:], sig)
	case ed25519.PublicKey:
		return ed25519.Verify(pub, data, sig)
	case *rsa.PublicKey:
		d := sha256.Sum256(data)
		return rsa.VerifyPKCS1v15(pub, crypto.SHA256, d[:], sig) == nil
	}
	return false
}

// ------------------------------------------------------------------------------------------------ the ceremonies

type clientData struct {
	Type      string `json:"type"`
	Challenge string `json:"challenge"`
	Origin    string `json:"origin"`
}

func checkClient(raw []byte, want string, challenge []byte, origin string) error {
	var c clientData
	if err := json.Unmarshal(raw, &c); err != nil {
		return errors.New("the client's data is not JSON")
	}
	if c.Type != want {
		return fmt.Errorf("the client's data is a %q, not a %q", c.Type, want)
	}
	got, err := b64.DecodeString(strings.TrimRight(c.Challenge, "="))
	if err != nil || subtle.ConstantTimeCompare(got, challenge) != 1 {
		return errors.New("it answers another challenge")
	}
	if c.Origin != origin {
		return fmt.Errorf("it was made for %q, not for %q", c.Origin, origin)
	}
	return nil
}

type authData struct {
	rpIDHash []byte
	flags    byte
	count    uint32
	credID   []byte
	cose     []byte
}

func parseAuthData(b []byte) (*authData, error) {
	if len(b) < 37 {
		return nil, errors.New("the authenticator's data is cut short")
	}
	a := &authData{rpIDHash: b[:32], flags: b[32], count: binary.BigEndian.Uint32(b[33:37])}
	if a.flags&flagAT != 0 {
		if len(b) < 55 {
			return nil, errors.New("the credential's data is cut short")
		}
		n := int(binary.BigEndian.Uint16(b[53:55]))
		if n == 0 || n > 1023 || len(b) < 55+n {
			return nil, errors.New("the credential's id is cut short, or longer than the standard allows")
		}
		a.credID = b[55 : 55+n]
		_, used, err := cbor(b[55+n:], 0)
		if err != nil {
			return nil, fmt.Errorf("the credential's key: %v", err)
		}
		a.cose = b[55+n : 55+n+used]
	}
	return a, nil
}

func checkAuth(a *authData, rpID string) error {
	h := sha256.Sum256([]byte(rpID))
	if !bytes.Equal(a.rpIDHash, h[:]) {
		return errors.New("it was made for another site")
	}
	if a.flags&flagUP == 0 {
		return errors.New("nobody was present at the authenticator")
	}
	// presence is not enough: the authenticator verified its holder — a PIN, a face, a finger — so a key found or
	// borrowed alone signs nobody in (security audit 2026-10-10, 1.3)
	if a.flags&flagUV == 0 {
		return errors.New("the authenticator did not verify its holder")
	}
	return nil
}

// Anchor is what the person's bean names: the credential id and the COSE key, base64url, joined by a dot.
func Anchor(credID, cose []byte) string {
	return b64.EncodeToString(credID) + "." + b64.EncodeToString(cose)
}

// ParseAnchor splits a bean's passkey name back into its credential id and key.
func ParseAnchor(s string) ([]byte, *Key, error) {
	id, k, ok := strings.Cut(s, ".")
	if !ok {
		return nil, nil, errors.New("a passkey's name is its credential id and its key, joined by a dot")
	}
	cid, err := b64.DecodeString(id)
	if err != nil {
		return nil, nil, err
	}
	cose, err := b64.DecodeString(k)
	if err != nil {
		return nil, nil, err
	}
	key, err := ParseKey(cose)
	return cid, key, err
}

// Register verifies a new passkey (navigator.credentials.create, attestation "none") and returns the anchor its
// person's bean will name.
func Register(clientDataJSON, attestationObject, challenge []byte, origin, rpID string) (string, error) {
	if err := checkClient(clientDataJSON, "webauthn.create", challenge, origin); err != nil {
		return "", err
	}
	v, n, err := cbor(attestationObject, 0)
	if err != nil || n != len(attestationObject) {
		return "", errors.New("the attestation is not one CBOR map")
	}
	m, ok := v.(map[any]any)
	if !ok {
		return "", errors.New("the attestation is not a map")
	}
	raw, _ := m["authData"].([]byte)
	a, err := parseAuthData(raw)
	if err != nil {
		return "", err
	}
	if err := checkAuth(a, rpID); err != nil {
		return "", err
	}
	if a.credID == nil {
		return "", errors.New("it carries no credential")
	}
	if _, err := ParseKey(a.cose); err != nil {
		return "", err
	}
	return Anchor(a.credID, a.cose), nil
}

// SignIn verifies a sign-in (navigator.credentials.get) by the credential `credID` against the anchors the person's
// bean names; it returns the anchor that signed, and the signature counter its authenticator signed with (for Counts:
// whether it grew is the caller's to ask, since only the caller keeps the last one).
func SignIn(credID, clientDataJSON, authenticatorData, signature, challenge []byte, origin, rpID string, anchors []string) (string, uint32, error) {
	if err := checkClient(clientDataJSON, "webauthn.get", challenge, origin); err != nil {
		return "", 0, err
	}
	a, err := parseAuthData(authenticatorData)
	if err != nil {
		return "", 0, err
	}
	if err := checkAuth(a, rpID); err != nil {
		return "", 0, err
	}
	h := sha256.Sum256(clientDataJSON)
	signed := append(append([]byte(nil), authenticatorData...), h[:]...)
	for _, s := range anchors {
		cid, key, err := ParseAnchor(s)
		if err != nil || !bytes.Equal(cid, credID) {
			continue
		}
		if key.Verify(signed, signature) {
			return s, a.count, nil
		}
		return "", 0, errors.New("the signature does not verify against the key the garden names")
	}
	return "", 0, errors.New("no passkey the garden names for this person is this one")
}
