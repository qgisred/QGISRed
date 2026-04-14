import pytest
from QGISRed.ui.analysis.qgisred_results_data import seconds_to_time_str

class TestResultsData:
    @pytest.mark.parametrize("seconds, expected", [
        (0, "0:00:00"),
        (1, "0:00:01"),
        (59, "0:00:59"),
        (60, "0:01:00"),
        (3599, "0:59:59"),
        (3600, "1:00:00"),
        (86399, "23:59:59"),
        (86400, "1d 0:00:00"),
        (90061, "1d 1:01:01"),
        (172800, "2d 0:00:00"),
    ])
    def test_seconds_to_time_str(self, seconds, expected):
        assert seconds_to_time_str(seconds) == expected

    def test_seconds_to_time_str_large(self):
        # 10 days = 10 * 86400 = 864000
        assert seconds_to_time_str(864000) == "10d 0:00:00"
