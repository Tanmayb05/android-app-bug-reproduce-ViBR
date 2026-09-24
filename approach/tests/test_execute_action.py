from approach.device.execute_action import execute_actions


class FakeDevice:
    def __init__(self):
        self.calls = []

    def click(self, x, y):
        self.calls.append(("click", x, y))

    def input_text(self, text):
        self.calls.append(("input_text", text))


def test_input_text_taps_position_before_typing():
    device = FakeDevice()

    execute_actions(
        device,
        [{"action": "input_text", "position": [10, 20], "text": "hello"}],
    )

    assert device.calls == [("click", 10, 20), ("input_text", "hello")]
