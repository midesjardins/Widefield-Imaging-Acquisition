import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import src.calculations as calc
import numpy as np
import scipy.signal as signal


class TestData(unittest.TestCase):
    def test_frames_acquired_from_camera_signal(self):
        """Test that the frames acquired from the camera signal are correctly calculated"""
        x_values = np.linspace(0, 5, 11)
        y_values = signal.square(2 * np.pi * x_values)
        np.testing.assert_array_equal(
            np.array([0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]),
            calc.frames_acquired_from_camera_signal(y_values),
        )

    def test_average_baseline(self):
        """Test that the baselines are correctly averaged"""
        frames = [np.array([[1, 2, 3], [4, 5, 6]]), np.array([[7, 8, 9], [10, 11, 12]])]
        np.testing.assert_array_equal(
            [np.array([[4, 5, 6], [7, 8, 9]])], calc.average_baseline(frames)
        )

    def test_get_baseline_frame_indices(self):
        """Test that the baseline frame indices are correctly calculated"""
        baseline_indices = [[0, 2], [3, 5], [6, 9]]
        frames_acquired = [0, 0, 0, 0, 0, 1, 1, 2, 3, 3]
        self.assertEqual(
            [[0, 0], [0, 1], [1, 3]],
            calc.get_baseline_frame_indices(baseline_indices, frames_acquired),
        )
        pass

    def test_map_activation(self):
        """Test that the activation is correctly mapped to the baseline"""
        frames = [np.array([[1, 2, 3], [4, 5, 6]]), np.array([[7, 8, 9], [10, 11, 12]])]
        baseline = np.array([[0, 3, 1], [1, 1, 1]])
        np.testing.assert_array_equal(
            [np.array([[1, -1, 2], [3, 4, 5]]), np.array([[7, 5, 8], [9, 10, 11]])],
            calc.map_activation(frames, baseline),
        )


if __name__ == "__main__":
    unittest.main()
