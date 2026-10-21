from PyQt6.QtCore import Qt, QPoint
from cmf_control.ui.widgets.custom_eq import CustomEQ, DotFader


def test_fader_keys_and_clamp(qtbot):
    f = DotFader("BASS")
    qtbot.addWidget(f)
    qtbot.keyClick(f, Qt.Key.Key_Up)
    assert f.value() == 1
    for _ in range(20):
        qtbot.keyClick(f, Qt.Key.Key_Up)
    assert f.value() == 6
    qtbot.keyClick(f, Qt.Key.Key_Home)
    assert f.value() == 0
    qtbot.keyClick(f, Qt.Key.Key_PageDown)
    assert f.value() == -6


def test_fader_click_maps_row_to_gain(qtbot):
    f = DotFader("BASS")
    qtbot.addWidget(f)
    f.resize(60, f.height())
    top_row = f._y_for(6)
    qtbot.mouseClick(f, Qt.MouseButton.LeftButton, pos=QPoint(30, int(top_row)))
    assert f.value() == 6


def test_drag_burst_sends_once(qtbot):
    w = CustomEQ()
    qtbot.addWidget(w)
    with qtbot.waitSignal(w.changed, timeout=1000) as sig:
        for v in (1, 2, 3):
            w._faders[0].setValue(v)
    assert sig.args == [3, 0, 0]


def test_set_values_from_device_does_not_echo(qtbot):
    w = CustomEQ()
    qtbot.addWidget(w)
    with qtbot.assertNotEmitted(w.changed, wait=400):
        w.set_values(2, -1, 4)
    assert w.values() == (2, -1, 4)
    assert w._flat.isEnabled()


def test_reset_to_flat_sends_zeros(qtbot):
    w = CustomEQ()
    qtbot.addWidget(w)
    w.set_values(2, -1, 4)
    with qtbot.waitSignal(w.changed, timeout=1000) as sig:
        w._flat.click()
    assert sig.args == [0, 0, 0]
    assert not w._flat.isEnabled()
