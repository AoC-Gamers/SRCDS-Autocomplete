#!/usr/bin/env python3
"""Resolve release naming as data; never publish, download, or modify Git refs."""
from __future__ import annotations
import argparse
import json
import os
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Identity:
    name: str
    platform: str
    platform_label: str
    channel: str
    basename: str
    filename: str
    release_tag: str | None
    release_name: str | None
    prerelease: bool
    make_latest: bool
    publishable: bool  # Eligible ref only; not authorization to publish.


def resolve(name: str, platform: str, ref_type: str = "local", ref: str = "",
            sha: str = "", local_channel: str = "local") -> Identity:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 80:
        raise ValueError("name must be a lowercase kebab-case product slug (max 80 characters)")
    if platform not in {"linux", "windows"}:
        raise ValueError("platform must be linux or windows")
    if ref_type not in {"branch", "tag", "local"}:
        raise ValueError("ref-type must be branch, tag or local")
    if local_channel not in {"local", "latest", "develop"}:
        raise ValueError("local-channel must be local, latest or develop")
    tag = title = None
    prerelease = latest = publishable = False
    if ref_type == "branch" and ref in {"main", "develop"}:
        channel = "latest" if ref == "main" else "develop"
        tag = f"channel/{channel}"
        title = "Latest" if ref == "main" else "Develop"
        prerelease = ref == "develop"
        latest = not prerelease
        publishable = True
    elif ref_type == "tag":
        # The reference routes v* to versioned releases. Bound the value to a safe
        # basename without assuming all projects use an identical SemVer scheme.
        if not re.fullmatch(r"v[0-9][0-9A-Za-z.+-]{0,79}", ref) or ".." in ref:
            raise ValueError("tag must be a safe v-prefixed version, e.g. v1.2.3")
        channel = ref[1:]
        tag, title, latest, publishable = ref, f"{name} {channel}", True, True
    elif ref_type == "local":
        channel = local_channel
    else:
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError("non-channel branches require a full 40-character commit SHA")
        channel = sha[:7].lower()
    label = platform
    basename = f"{name}-{channel}-{label}"
    return Identity(name, platform, label, channel, basename, basename + ".zip",
                    tag, title, prerelease, latest, publishable)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=os.getenv("AOC_PROJECT_NAME", "example"))
    parser.add_argument("--platform", default=os.getenv("AOC_PLATFORM", "linux"))
    parser.add_argument("--ref-type", default=os.getenv("AOC_REF_TYPE", "local"))
    parser.add_argument("--ref", default=os.getenv("AOC_REF_NAME", ""))
    parser.add_argument("--sha", default=os.getenv("AOC_COMMIT_SHA", ""))
    parser.add_argument("--local-channel", default=os.getenv("AOC_LOCAL_CHANNEL", "local"))
    args = parser.parse_args()
    try:
        result = resolve(args.name, args.platform, args.ref_type, args.ref,
                         args.sha, args.local_channel)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
