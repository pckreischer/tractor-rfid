import pytest

from tractor_rfid.backends.dry_run import DryRunBackend
from tractor_rfid.hid.keycodes import char_to_usage
from tractor_rfid.macro.loader import load_profile
from tractor_rfid.macro.model import Macro, Profile, Screen, Step
from tractor_rfid.macro.runner import MacroRunner

PROFILE = "profiles/gen4.yaml"


def kinds(backend):
    return [e.kind for e in backend.transcript]


def texts(backend):
    return [e.detail["value"] for e in backend.transcript if e.kind == "text"]


def test_profile_loads_with_expected_macros():
    p = load_profile(PROFILE)
    assert p.display == "gen4"
    assert p.macro("set_seed_variety").params == ["crop", "variety"]


def test_unknown_action_is_rejected():
    with pytest.raises(ValueError, match="unknown action"):
        Step("frobnicate", {})


def test_parameters_are_substituted():
    step = Step("text", {"value": "{variety}"}).resolve({"variety": "P1197AM"})
    assert step.args["value"] == "P1197AM"


def test_missing_parameter_names_itself():
    macro = Macro("m", params=["variety"], steps=[])
    with pytest.raises(KeyError, match="variety"):
        list(macro.bind({}))


def test_undefined_placeholder_is_an_error_not_a_silent_blank():
    with pytest.raises(KeyError, match="typo"):
        Step("text", {"value": "{typo}"}).resolve({"variety": "x"})


def test_run_types_the_bound_value():
    profile = load_profile(PROFILE)
    backend = DryRunBackend()
    MacroRunner(profile, backend).run(
        "set_seed_variety", {"crop": "Corn", "variety": "P1197AM"}
    )
    assert "P1197AM" in texts(backend)


def test_goto_always_replays_the_reset_sequence_first():
    profile = Profile(
        display="t",
        reset=[Step("key", {"name": "ESC"})],
        screens={"s": Screen("s", [Step("tap", {"x": 1, "y": 2})])},
    )
    backend = DryRunBackend()
    MacroRunner(profile, backend).goto("s")
    # ESC (reset) must precede the tap that walks the path.
    assert kinds(backend).index("key") < kinds(backend).index("tap")


def test_goto_inside_a_navigation_path_is_rejected():
    profile = Profile(
        display="t", screens={"s": Screen("s", [Step("goto", {"screen": "s"})])}
    )
    with pytest.raises(ValueError, match="not allowed"):
        MacroRunner(profile, DryRunBackend()).goto("s")


def test_unknown_screen_lists_the_known_ones():
    profile = Profile(display="t", screens={"work_setup": Screen("work_setup")})
    with pytest.raises(KeyError, match="work_setup"):
        profile.screen("nope")


@pytest.mark.parametrize("ch,shift", [("a", False), ("A", True), ("5", False), ("%", True)])
def test_hid_shift_detection(ch, shift):
    assert char_to_usage(ch)[1] is shift


def test_unmappable_character_raises_rather_than_dropping():
    with pytest.raises(ValueError, match="no US-layout"):
        char_to_usage("é")
