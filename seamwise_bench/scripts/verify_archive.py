#!/usr/bin/env python3
"""Verify archive hash and all member hashes without extracting files."""
import sys,pathlib,json,tarfile,hashlib
p=pathlib.Path(sys.argv[1]);expected=p.with_suffix(p.suffix+'.sha256').read_text().split()[0]
digest=hashlib.sha256()
with p.open('rb') as f:
    while chunk:=f.read(1024*1024):digest.update(chunk)
assert digest.hexdigest()==expected,'Archive SHA256 mismatch'
with tarfile.open(p,'r:gz') as tar:
    manifest=json.load(tar.extractfile('seamwise_bench/evidence/archive_manifest.json'));seen=set()
    for member in tar:
        if member.isfile() and member.name in manifest['files']:
            assert member.name not in seen,'Duplicate member'
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==manifest['files'][member.name],member.name
            seen.add(member.name)
    assert seen==set(manifest['files']),'Missing member'
print(f'PASS: archive SHA256 and {len(seen)} regular-member hashes')
