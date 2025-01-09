import unittest
from unittest.mock import patch
from datetime import datetime
from charge_history_to_csv import get_pricing, get_fixed_pricing, get_agile_pricing


class TestGetPricing(unittest.TestCase):

    @patch("charge_history_to_csv.get_fixed_pricing")
    @patch("charge_history_to_csv.get_agile_pricing")
    def test_get_pricing_fixed(self, mock_get_agile_pricing, mock_get_fixed_pricing):
        start = datetime(2024, 9, 3)
        end = datetime(2024, 9, 1)

        mock_get_fixed_pricing.return_value = {start: 25.01}

        result = get_pricing(start, end)

        mock_get_fixed_pricing.assert_called_once_with(start, end)
        mock_get_agile_pricing.assert_not_called()
        self.assertEqual(result, {start: 25.01})

    @patch("charge_history_to_csv.get_fixed_pricing")
    @patch("charge_history_to_csv.get_agile_pricing")
    def test_get_pricing_agile(self, mock_get_agile_pricing, mock_get_fixed_pricing):
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 2)

        mock_get_agile_pricing.return_value = {start: 0.15}

        result = get_pricing(start, end)

        mock_get_agile_pricing.assert_called_once_with(start, end)
        mock_get_fixed_pricing.assert_not_called()
        self.assertEqual(result, {start: 0.15})


class TestGetFixedPricing(unittest.TestCase):

    def test_get_fixed_pricing_single_interval(self):
        start = datetime(2024, 9, 3, 12, 10, 36, 123)
        end = datetime(2024, 9, 3, 12, 20)

        result = get_fixed_pricing(start, end)

        expected = {"2024-09-03T12:00:00": 25.01}

        self.assertEqual(result, expected)

    def test_get_fixed_pricing_multiple_intervals(self):
        start = datetime(2024, 9, 3, 12, 10, 36, 123)
        end = datetime(2024, 9, 3, 19, 31)

        result = get_fixed_pricing(start, end)

        expected = {
            "2024-09-03T12:00:00": 25.01,
            "2024-09-03T12:30:00": 25.01,
            "2024-09-03T13:00:00": 25.01,
            "2024-09-03T13:30:00": 25.01,
            "2024-09-03T14:00:00": 25.01,
            "2024-09-03T14:30:00": 25.01,
            "2024-09-03T15:00:00": 25.01,
            "2024-09-03T15:30:00": 25.01,
            "2024-09-03T16:00:00": 25.01,
            "2024-09-03T16:30:00": 25.01,
            "2024-09-03T17:00:00": 25.01,
            "2024-09-03T17:30:00": 25.01,
            "2024-09-03T18:00:00": 25.01,
            "2024-09-03T18:30:00": 25.01,
            "2024-09-03T19:00:00": 25.01,
            "2024-09-03T19:30:00": 25.01,
        }

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
