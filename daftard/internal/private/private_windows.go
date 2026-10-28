//go:build windows

package private

import (
	"errors"
	"fmt"
	"os"
	"syscall"
	"unsafe"
)

// ON WINDOWS a file is this account's alone where its access list (its DACL, read with advapi32's own
// GetNamedSecurityInfoW, through the standard library's syscall) lets nobody but this account read or change it — and
// SYSTEM and the Administrators, who may reach every file on the machine, as root may on Linux. An entry that only
// passes on to what is made inside (inherit-only) grants nothing here; one that grants only a file's attributes or its
// access list's reading reveals nothing of it.
var (
	advapi32              = syscall.NewLazyDLL("advapi32.dll")
	getNamedSecurityInfoW = advapi32.NewProc("GetNamedSecurityInfoW")
	localFree             = syscall.NewLazyDLL("kernel32.dll").NewProc("LocalFree")
)

const (
	seFileObject             = 1
	ownerSecurityInformation = 0x1
	daclSecurityInformation  = 0x4
	accessAllowedACEType     = 0
	inheritOnlyACE           = 0x8
	// what lets another read, change or remove a file or a folder: its data (a folder's list, its adding), deleting it,
	// changing its access list or its owner, and the generic rights that include them
	reaches = 0x1 | 0x2 | 0x4 | 0x10000 | 0x40000 | 0x80000 | 0x10000000 | 0x40000000 | 0x80000000
)

// acl and aceHeader are winnt.h's ACL and ACE_HEADER; an ACCESS_ALLOWED_ACE is its header, its mask (4 bytes) and its
// SID from offset 8.
type acl struct {
	revision, sbz1 byte
	size, count    uint16
	sbz2           uint16
}

type aceHeader struct {
	kind, flags byte
	size        uint16
}

// trusted are the accounts that may reach any file of the machine: SYSTEM, and the Administrators group.
var trusted = map[string]bool{"S-1-5-18": true, "S-1-5-32-544": true}

// Check says why path is not this account's alone — an entry of its access list lets another account read or change
// it, or it has no access list at all (anyone may) — and nil where it is.
func Check(path string) error {
	me, err := account()
	if err != nil {
		return fmt.Errorf("this account's own SID: %v", err)
	}
	p, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return err
	}
	var owner *syscall.SID
	var dacl *acl
	var sd uintptr
	r, _, _ := getNamedSecurityInfoW.Call(uintptr(unsafe.Pointer(p)), seFileObject,
		ownerSecurityInformation|daclSecurityInformation, uintptr(unsafe.Pointer(&owner)), 0,
		uintptr(unsafe.Pointer(&dacl)), 0, uintptr(unsafe.Pointer(&sd)))
	if r != 0 {
		return fmt.Errorf("%s: its access list cannot be read: %v", path, syscall.Errno(r))
	}
	defer localFree.Call(sd)
	if dacl == nil {
		return errors.New(path + " has no access list: anyone may read and change it")
	}
	ownerSID := ""
	if owner != nil {
		ownerSID, _ = owner.String()
	}
	ace := unsafe.Add(unsafe.Pointer(dacl), unsafe.Sizeof(acl{}))
	for i := 0; i < int(dacl.count); i++ {
		h := (*aceHeader)(ace)
		if h.kind == accessAllowedACEType && h.flags&inheritOnlyACE == 0 {
			mask := *(*uint32)(unsafe.Add(ace, 4))
			sid, err := (*syscall.SID)(unsafe.Add(ace, 8)).String()
			if err != nil {
				return fmt.Errorf("%s: an entry of its access list names no SID: %v", path, err)
			}
			// OWNER RIGHTS (S-1-3-4) is whoever owns it: this account's own where it owns it
			mine := sid == me || trusted[sid] || sid == "S-1-3-4" && ownerSID == me
			if mask&reaches != 0 && !mine {
				return fmt.Errorf("%s may be reached by %s (access mask %#x), not this account (%s) alone", path, sid, mask, me)
			}
		}
		if h.size == 0 {
			break
		}
		ace = unsafe.Add(ace, int(h.size))
	}
	return nil
}

// account is this process's account, as a SID string.
func account() (string, error) {
	t, err := syscall.OpenCurrentProcessToken()
	if err != nil {
		return "", err
	}
	defer t.Close()
	u, err := t.GetTokenUser()
	if err != nil {
		return "", err
	}
	return u.User.Sid.String()
}

var convertSDDL = advapi32.NewProc("ConvertStringSecurityDescriptorToSecurityDescriptorW")

// create makes a new file at path, this account's alone from its first byte: its access list its own (protected, so
// nothing its folder would pass on applies), granting all of it to this account, to SYSTEM and to the Administrators —
// those Check trusts — and nobody else. A security descriptor given to CreateFile applies to a file it makes; that is
// why the file is new (CREATE_NEW), and WriteFile puts it in place of any copy there before.
func create(path string) (*os.File, error) {
	me, err := account()
	if err != nil {
		return nil, fmt.Errorf("this account's own SID: %v", err)
	}
	sddl, err := syscall.UTF16PtrFromString("D:P(A;;FA;;;" + me + ")(A;;FA;;;SY)(A;;FA;;;BA)")
	if err != nil {
		return nil, err
	}
	var sd uintptr
	if r, _, e := convertSDDL.Call(uintptr(unsafe.Pointer(sddl)), 1, uintptr(unsafe.Pointer(&sd)), 0); r == 0 {
		return nil, fmt.Errorf("an access list for %s alone: %v", me, e)
	}
	defer localFree.Call(sd)
	p, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	sa := &syscall.SecurityAttributes{Length: uint32(unsafe.Sizeof(syscall.SecurityAttributes{})), SecurityDescriptor: sd}
	h, err := syscall.CreateFile(p, syscall.GENERIC_WRITE, 0, sa, syscall.CREATE_NEW, syscall.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		return nil, &os.PathError{Op: "create", Path: path, Err: err}
	}
	return os.NewFile(uintptr(h), path), nil
}
