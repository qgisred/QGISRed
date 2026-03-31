import pytest
from QGISRed.ui.analysis.qgisred_results_data import seconds_to_time_str

class TestResultsData:
    @pytest.mark.parametrize("seconds, expected", [
        (0, "00d 00:00:00"),
        (1, "00d 00:00:01"),
        (59, "00d 00:00:59"),
        (60, "00d 00:01:00"),
        (3599, "00d 00:59:59"),
        (3600, "00d 01:00:00"),
        (86399, "00d 23:59:59"),
        (86400, "01d 00:00:00"),
        (90061, "01d 01:01:01"),
        (172800, "02d 00:00:00"),
    ])
    def test_seconds_to_time_str(self, seconds, expected):
        assert seconds_to_time_str(seconds) == expected

    def test_seconds_to_time_str_large(self):
        # 10 days = 10 * 86400 = 864000
        assert seconds_to_time_str(864000) == "10d 00:00:00"
