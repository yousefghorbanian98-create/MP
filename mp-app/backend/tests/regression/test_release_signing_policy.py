"""Release pipeline must never fall back to the public debug signing key."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_gradle_release_uses_only_dedicated_signing_environment():
    gradle = (ROOT / "mp-app/client/android/app/build.gradle.kts").read_text()
    assert 'signingConfig = signingConfigs.getByName("release")' in gradle
    assert 'signingConfigs.getByName("debug")' not in gradle
    for variable in (
        "MP_ANDROID_KEYSTORE_PATH",
        "MP_ANDROID_STORE_PASSWORD",
        "MP_ANDROID_KEY_ALIAS",
        "MP_ANDROID_KEY_PASSWORD",
    ):
        assert f'System.getenv("{variable}")' in gradle


def test_release_build_is_guarded_and_audits_all_output_apks():
    workflow = yaml.safe_load((ROOT / ".github/workflows/apk.yml").read_text())
    jobs = workflow["jobs"]
    assert set(jobs) == {"apk"}  # no automatic publication or binary commits
    steps = jobs["apk"]["steps"]
    by_name = {step.get("name"): step for step in steps}
    prepare = by_name["Prepare dedicated release signing material"]
    assert set(prepare["env"]) == {
        "KEYSTORE_B64",
        "MP_ANDROID_STORE_PASSWORD",
        "MP_ANDROID_KEY_ALIAS",
        "MP_ANDROID_KEY_PASSWORD",
    }
    assert "refusing debug signing" in prepare["run"]
    verify = by_name["Verify release signer on every APK"]
    assert "apksigner" in verify["run"]
    assert "MP_ANDROID_CERT_SHA256" in verify["env"]["EXPECTED_CERT_SHA256"]
    assert "app-*-release.apk" in verify["run"]
    audit = by_name["Deep APK audit (apktool)"]
    assert ' --apk "$apk"' in audit["run"]
    assert "app-*-release.apk" in audit["run"]
    cleanup = by_name["Delete temporary release signing material"]
    assert cleanup["if"] == "always()"
