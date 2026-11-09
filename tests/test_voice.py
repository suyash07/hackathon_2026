import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from voice import SPOKEN, TYPED, pick_question  # noqa: E402


def test_new_typed_question_beats_old_recording():
    assert pick_question("new typed", "old spoken", TYPED) == "new typed"


def test_new_recording_beats_old_typed_question():
    assert pick_question("old typed", "new spoken", SPOKEN) == "new spoken"


def test_falls_back_when_last_source_is_empty():
    assert pick_question("typed", "", SPOKEN) == "typed"
    assert pick_question("", "spoken", TYPED) == "spoken"


def test_no_source_yet_uses_whichever_is_filled():
    assert pick_question("", "spoken", None) == "spoken"
    assert pick_question("typed", "", None) == "typed"


def test_nothing_entered():
    assert pick_question("", "", None) == ""
