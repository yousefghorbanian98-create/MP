"""Release pipeline must never fall back to the public debug signing key."""

from pathlib import Path

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
