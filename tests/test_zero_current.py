"""zero_current must not rewrite calibration from an incomplete U reply."""
import json
import unittest
from unittest.mock import MagicMock

from server.command_server import CommandServer


def make_server(cal):
    mc = MagicMock()
    mc._gpio.get_calibration.return_value = cal
    mc._gpio.set_calibration.side_effect = lambda ch, g, o: (ch, g, o)
    return CommandServer(mc, MagicMock(), port=0), mc._gpio


def zero(server, measured=(0.001, 0.002, 0.003, 0.004)):
    line = json.dumps({"cmd": "zero_current", "measured_a": list(measured)})
    return server._dispatch(line, None)


class TestZeroCurrent(unittest.TestCase):
    def test_folds_residual_and_keeps_gain(self):
        cal = {0: (0.99, 0.0), 1: (0.70, 0.0), 2: (0.84, 0.0), 3: (0.89, 0.0)}
        server, gpio = make_server(cal)
        self.assertTrue(zero(server)["ok"])
        self.assertEqual(gpio.set_calibration.call_count, 4)
        ch, gain, offset = gpio.set_calibration.call_args_list[3].args
        self.assertEqual((ch, gain), (3, 0.89))
        self.assertAlmostEqual(offset, -0.004)

    def test_missing_channel_writes_nothing(self):
        server, gpio = make_server({0: (0.99, 0.0), 1: (0.70, 0.0), 2: (0.84, 0.0)})
        self.assertFalse(zero(server)["ok"])
        gpio.set_calibration.assert_not_called()

    def test_failed_query_writes_nothing(self):
        server, gpio = make_server(None)
        self.assertFalse(zero(server)["ok"])
        gpio.set_calibration.assert_not_called()


if __name__ == "__main__":
    unittest.main()
