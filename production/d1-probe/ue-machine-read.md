# Reading the UE machine probe, run 2 (2026-09-01)

Raw output: production/d1-probe/ue-machine.txt. This is the reading, kept
separate so the measurement stays a measurement.

## What is there
UE 5.8 at C:\Program Files\Epic Games\UE_5.8, with UnrealEditor-Cmd.exe
present beside it. That binary is the headless editor, and its presence is
what makes a CI-driven UE build possible at all: measurement b can be taken
without anybody opening a window.

dotnet 8.0.424 is on PATH. Disk is ample: C has 87 GB free and F has 105 GB,
against the tens of GB a UE project plus derived data wants.

## What is missing, and it blocks the C++ half
msvc NOT FOUND, and the stronger form of it: vswhere is absent, so there is
no Visual Studio installation of any kind on the machine. UE cannot compile
a C++ project without MSVC. This does not block a Blueprint-only or
content-only UE run, and it does block D1's transliteration task (001),
which is C++ by definition.

This is a FINDING FOR MEASUREMENT a, not a broken probe: setup cost is part
of what the probe exists to measure, and "the machine needed a 10 to 20 GB
toolchain install before the first line of C++ could compile" is exactly the
kind of friction D1 is comparing between engines. Unity needed no such step.

## The phantom entry, named so nobody chases it
ueInstalls=2, and the first is `version=4.0 path=C:\Program Files\Epic
Games\4.0\ editorCmd=False`. That is a registry leftover, not an install:
no editor binary under it. The probe reports what it finds rather than what
it believes, which is correct, and the reading is where the judgement goes.

## The instrument fault this run exposed
Line 1 read `# UE machine probe -  @1788263890`, with the sha EMPTY. The
provenance line every verdict in this project carries had no provenance.
`git rev-parse --short HEAD` returned nothing inside the pwsh step and
ErrorActionPreference=Continue swallowed the reason. Fixed to read
GITHUB_SHA, which Actions sets itself and which cannot be empty in a real
run, with git as fallback and the literal SHA-UNKNOWN if both fail, because
a blank where a sha belongs is worse than a word saying it is missing.
