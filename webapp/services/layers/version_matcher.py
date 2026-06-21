# webapp/services/layers/version_matcher.py

from packaging.version import Version

def find_best_version_match(target_version, available_versions):
    try:
        target = Version(target_version)
    except Exception:
        return None

    parsed = []
    for version in available_versions:
        try:
            parsed.append(Version(version))
        except Exception:
            continue

    if not parsed:
        return None

    same_major = [v for v in parsed if v.major == target.major]

    if not same_major:
        return None

    same_minor = [v for v in same_major if v.minor == target.minor]

    if same_minor:
        same_minor.sort(key=lambda v: abs(v.micro - target.micro))
        return str(same_minor[0])

    # fallback:
    same_major.sort(key=lambda v: abs(v.minor - target.minor))
    return str(same_major[0])