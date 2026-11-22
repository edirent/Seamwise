#!/usr/bin/env python3
"""Seal only after all measurement and analysis jobs have stopped writing."""
import sys,pathlib,json,subprocess,collections,tarfile,hashlib,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic,sha

def main():
    original=json.loads((ROOT/'evidence/original_sha256.json').read_text())
    assert all((ROOT.parent/p).is_file() and sha(ROOT.parent/p)==h for p,h in original.items()),'Historical content changed'
    ledgers=[]
    for p in sorted((ROOT/'results').glob('*/execution_ledger.json')):
        for row in json.loads(p.read_text()):ledgers.append(dict(row,run=str(p.parent.relative_to(ROOT))))
    atomic(ROOT/'evidence/full_execution_ledger.json',dict(jobs=ledgers,status_counts=dict(collections.Counter(r['status'] for r in ledgers)),
        command_failures=json.loads((ROOT/'evidence/command_failures.json').read_text()),
        interpretation='job-level counts include reused fixtures, repetitions, aborted runs and deliberate deferred cells; never a count of independent shots'))
    env=json.loads((ROOT/'evidence/doctor_confirmatory.log').read_text())
    binaries={str(p.relative_to(ROOT)):sha(p) for directory in ['build','build_v1','build_v2','build_v3','build_gprof'] for p in (ROOT/directory).glob('*') if p.is_file() and (p.suffix=='.so' or p.name in ['native_runner','native_tests','alloc_audit_contract','compile_commands.json','CMakeCache.txt'])}
    wheels={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'evidence/wheels').glob('*') if p.is_file()}
    vendor_sources={}
    for name in ['gari','ldpc','relay','tesseract']:
        base=ROOT/'vendor'/name
        commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        status=subprocess.check_output(['git','-C',str(base),'status','--porcelain','--untracked-files=no'],text=True)
        changed=subprocess.check_output(['git','-C',str(base),'diff','--name-only'],text=True).splitlines()
        source_changes=[p for p in changed if pathlib.Path(p).suffix in ['.c','.cc','.cpp','.h','.hpp','.rs','.py']]
        assert not source_changes,(name,source_changes)
        vendor_sources[name]=dict(commit=commit,tracked_changes=status,tracked_source_changes=source_changes,official_source=True,
            note='GARI tracked hbplib_v2.so is a rebuilt binary; upstream C source is unchanged. First-party adapters live outside vendor.')
    atomic(ROOT/'evidence/toolchain_dependency_lock.json',dict(environment=env,source_repositories=vendor_sources,binaries=binaries,wheels=wheels,
        requirements_sha256=sha(ROOT/'requirements.lock'),cmake_sha256=sha(ROOT/'CMakeLists.txt'),
        compilation='portable release C++20 -O3 -DNDEBUG -fno-fast-math -ffp-contract=off; flags per compile_commands; gprof/sanitizers diagnostic only',
        wheels_policy='Tesseract/Relay official-source wheels override nominal PyPI version; see README and wheel hashes'))
    chosen={ROOT.parent/p for p in original}
    for directory in ['cpp','python','tests','scripts','configs','evidence','results']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name!='archive_manifest.json' and not p.name.endswith('.tmp'):chosen.add(p)
    for p in ROOT.iterdir():
        if p.is_file():chosen.add(p)
    for directory in ['build','build_v1','build_v2','build_v3','build_gprof']:
        for p in (ROOT/directory).iterdir():
            if p.is_file() and (p.suffix=='.so' or p.name in ['native_runner','native_tests','alloc_audit_contract','compile_commands.json','CMakeCache.txt']):chosen.add(p)
    for name in ['gari','ldpc','relay','tesseract']:
        base=ROOT/'vendor'/name
        names=subprocess.check_output(['git','-C',str(base),'ls-files','-z']).decode().split('\0')
        for name_ in names:
            if name_ and (base/name_).is_file() and not (base/name_).is_symlink():chosen.add(base/name_)
    for name in ['ldpc-2.4.1.tar.gz','relay-bp-0.2.2.tar.gz','bazelisk']:
        p=ROOT/'vendor'/name
        if p.is_file():chosen.add(p)
    # Source-only unpacked official distributions retain provenance inputs.
    for name in ['ldpc-pypi','relay-pypi']:
        for p in (ROOT/'vendor'/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:chosen.add(p)
    entries={str(p.relative_to(ROOT.parent)):sha(p) for p in sorted(chosen)}
    manifest=ROOT/'evidence/archive_manifest.json'
    atomic(manifest,dict(schema=1,files=entries,original_unchanged_files=len(original),
        exclusions=['virtualenv','VCS object databases','Bazel/Cargo/CMake intermediates','new bytecode caches'],
        validation='SHA256 of every regular member except this manifest; archive hash in sibling .sha256 file'))
    chosen.add(manifest);artifact=ROOT/'artifacts';artifact.mkdir(exist_ok=True)
    dest=artifact/'seamwise_native_research_20261109.tar.gz'
    if dest.exists():raise RuntimeError('Refusing to overwrite sealed archive')
    with tarfile.open(dest,'w:gz',compresslevel=5) as tar:
        for p in sorted(chosen):tar.add(p,arcname=str(p.relative_to(ROOT.parent)),recursive=False)
    # Verify stream contents, not merely the original input list.
    with tarfile.open(dest,'r:gz') as tar:
        seen=set()
        for m in tar:
            if m.isfile() and m.name in entries:
                assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==entries[m.name],m.name
                seen.add(m.name)
        assert seen==set(entries),'Missing archive members'
    checksum=sha(dest);dest.with_suffix(dest.suffix+'.sha256').write_text(checksum+'  '+dest.name+'\n')
    atomic(artifact/'archive_verification.json',dict(status='PASS',archive=dest.name,sha256=checksum,bytes=dest.stat().st_size,verified_regular_members=len(entries),original_files_unchanged=len(original)))
    print(json.dumps(dict(archive=str(dest),sha256=checksum,files=len(entries))))
if __name__=='__main__':main()
