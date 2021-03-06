import logging
from unittest import TestCase
from MLX90621 import Blob, Pixel, MLX90621
import numpy as np


class TestMLX90621(TestCase):
    test_frame_0 = np.full((4, 16), 0)
    test_frame_1 = np.full((4, 16), 1)
    test_frame_2 = np.full((4, 16), 2)
    test_frame_3 = np.full((4, 16), 3)
    test_frame_4 = np.full((4, 16), 4)

    def setUp(self):
        log = logging.getLogger("MLX90621")
        x = list(log.handlers)
        for i in x:
            log.removeHandler(i)
            i.flush
            i.close

    def test__add_weighted_frame_to_background(self):
        """
        Test the cheap and nasty way of calculating the weighted frame average
        :return:
        """
        test_sensor = MLX90621(running_average_size=4)

        # Test - First frames become the new average
        test_sensor.pixel_averages = self.test_frame_2
        test_sensor.add_weighted_frame_to_background(self.test_frame_2)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, self.test_frame_2), True)

        # Test - averages behave as expected
        # Adding a 0 frame will result in a set of {2, 2, 2, 0}; average=1.5
        test_sensor.add_weighted_frame_to_background(self.test_frame_0)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, self.test_frame_0), False)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, self.test_frame_2), False)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 1.5)), True)

        # Test - averages behave as expected
        # A second zero should result in a weighted average of 1.125
        test_sensor.add_weighted_frame_to_background(self.test_frame_0)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 1.125)), True)

        # Test - averages behave as expected
        # A third zero should result in a weighted average of 0.84375
        test_sensor.add_weighted_frame_to_background(self.test_frame_0)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 0.84375)), True)

        # Test - averages behave as expected
        # A third zero should result in a weighted average of 0.84375
        test_sensor.add_weighted_frame_to_background(self.test_frame_4)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 1.6328125)), True)

    def test_add_frame_to_average(self):
        """
        Test that the average and standard deviations are calculated correctly as more frames are added to the running
        average.
        :return: None
        """
        test_sensor = MLX90621(running_average_size=4)

        # Running frames = [0], Avg. 0, Std. 0
        test_sensor.add_frame_to_average(self.test_frame_0)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, self.test_frame_0), True)
        self.assertEqual(np.array_equal(test_sensor.pixel_variance, np.full((4, 16), 0)), True)

        # Running frames = [0, 1], Avg. 0.5, Std. 0.5
        test_sensor.add_frame_to_average(self.test_frame_1)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 0.5)), True)
        self.assertEqual(np.array_equal(test_sensor.pixel_variance, np.full((4, 16), 0.5)), True)

        # Running frames = [0, 1, 2], Avg. 1, Std. 0.8165
        test_sensor.add_frame_to_average(self.test_frame_2)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 1)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 0.8165)), True)

        # Running frames = [0, 1, 2, 3], Avg. 1.5, Std. 1.11803
        test_sensor.add_frame_to_average(self.test_frame_3)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 1.5)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 1.11803)), True)

        # Running frames = [1, 2, 3, 4], Avg. 2.5, Std. 1.11803
        test_sensor.add_frame_to_average(self.test_frame_4)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 2.5)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 1.11803)), True)

        # Running frames = [2, 3, 4, 4], Avg. 3.25, Std. 0.82916
        test_sensor.add_frame_to_average(self.test_frame_4)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 3.25)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 0.82916)), True)

        # Running frames = [3, 4, 4, 4], Avg. 3.75, Std. 0.43301
        test_sensor.add_frame_to_average(self.test_frame_4)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 3.75)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 0.43301)), True)

        # Running frames = [4, 4, 4, 4], Avg. 4, Std. 0
        test_sensor.add_frame_to_average(self.test_frame_4)
        self.assertEqual(np.array_equal(test_sensor.pixel_averages, np.full((4, 16), 4)), True)
        self.assertEqual(np.allclose(test_sensor.pixel_variance, np.full((4, 16), 0)), True)

    def test_find_active_pixels(self):
        """
        Test active pixel extraction from a frame, given an existing running average
        :return:
        """
        test_sensor = MLX90621(running_average_size=2)

        # Clear the running average to all zeroes
        test_sensor.add_frame_to_average(self.test_frame_0)
        test_sensor.add_frame_to_average(self.test_frame_0)

        # Test frame - 7 active pixels against a 0 running background
        test_frame = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                               [0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 5, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 5, 0, 0, 0],
                               [0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        active_pixels = test_sensor.find_active_pixels(test_frame)
        self.assertEqual(len(active_pixels), 7)

        # Average: 1.5, std. deviation: 0.5
        # Values must be 1.5 above the mean for detection
        test_sensor.add_frame_to_average(self.test_frame_1)
        test_sensor.add_frame_to_average(self.test_frame_2)

        # Test frame - 4 active pixels against a running background of 1.5 (with 3* 0.5 std. dev threshold)
        test_frame_2 = np.array([[0, 0, 0, 9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                                 [0, 0, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 9, 0],
                                 [0, 0, 0, 0, 0, 0, 1, 2.8, 0, 0, 0, 0, 2, 0, 9, 0],
                                 [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        active_pixels = test_sensor.find_active_pixels(test_frame_2)
        self.assertEqual(len(active_pixels), 4)

    def test_find_blobs(self):
        """
        Test blob extraction from a frame
        :return:
        """
        test_sensor = MLX90621(running_average_size=2)
        test_sensor.add_frame_to_average(self.test_frame_0)
        test_sensor.add_frame_to_average(self.test_frame_0)

        # 7 non-zero values; 3 blobs
        test_frame = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 2, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 2, 0, 0, 0],
                               [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        blobs = test_sensor.find_blobs(test_frame)
        for blob in blobs:
            print("Blob size: {}".format(len(blob.pixels)))
            for pixel in blob.pixels:
                print pixel
            print("\n\n")

        self.assertEqual(len(blobs), 3)

        # 20 non-zero values; 4 blobs
        test_frame = np.array([[3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
                               [0, 0, 0, 0, 0, 0, 11, 11, 11, 11, 11, 11, 11, 0, 0, 4],
                               [0, 0, 0, 0, 0, 0, 11, 11, 0, 0, 0, 0, 11, 0, 0, 4],
                               [0, 2, 2, 0, 0, 0, 11, 0, 0, 0, 0, 0, 0, 0, 0, 4]])

        blobs = test_sensor.find_blobs(test_frame)
        for blob in blobs:
            print("Blob size: {}".format(len(blob.pixels)))
            for pixel in blob.pixels:
                print pixel
            print("\n\n")
        self.assertEqual(len(blobs), 4)

    def test_track_blobs(self):
        test_frame0 = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        test_frame1 = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        test_frame2 = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        test_frame3 = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        test_frame4 = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

        tracked_blobs = []

        # Set up playing field
        test_sensor = MLX90621(running_average_size=2, log_level=logging.DEBUG)
        test_sensor.add_frame_to_average(test_frame0)
        test_sensor.add_frame_to_average(test_frame0)
        self.assertEqual(test_sensor.net_passes, 0)

        # First frame - new blob at 1.5, 1.5
        new_blobs = test_sensor.find_blobs(test_frame1)
        self.assertAlmostEqual(len(new_blobs), 1)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 1)

        # Second frame - blob moves to 7.5, 1.5
        new_blobs = test_sensor.find_blobs(test_frame2)
        self.assertAlmostEqual(len(new_blobs), 1)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 1)
        self.assertEqual(tracked_blobs[0].travel[1], 5)

        # Third frame - blob moves to 12.5, 1.5
        new_blobs = test_sensor.find_blobs(test_frame3)
        self.assertAlmostEqual(len(new_blobs), 1)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 1)
        self.assertEqual(tracked_blobs[0].travel[1], 10)

        # Fourth frame - blob moves to 15, 1.5, half gone; may not recognise
        new_blobs = test_sensor.find_blobs(test_frame4)
        self.assertAlmostEqual(len(new_blobs), 1)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 1)
        self.assertEqual(tracked_blobs[0].travel[1], 13.5)

         # Fourth frame - blob moves to 15, 1.5, half gone; may not recognise
        new_blobs = test_sensor.find_blobs(test_frame4)
        self.assertAlmostEqual(len(new_blobs), 1)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 1)
        self.assertEqual(tracked_blobs[0].travel[1], 13.5)

        # Back to zero frame - Blob should now count as a rightward pass
        self.assertEqual(test_sensor.right_passes, 0)
        new_blobs = test_sensor.find_blobs(test_frame0)
        self.assertEqual(len(new_blobs), 0)
        tracked_blobs = test_sensor.track_blobs(tracked_blobs, new_blobs)
        self.assertEqual(len(tracked_blobs), 0)
        self.assertEqual(test_sensor.right_passes, 1)










