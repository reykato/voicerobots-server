import time
import threading
import unittest
from unittest.mock import MagicMock
from decisionmaker import DecisionMaker

class DecisionMaker_Test(unittest.TestCase):

    def setUp(self):
        # Mocking dependencies
        self.vsh_mock = MagicMock()
        self.lsh_mock = MagicMock()
        self.cs_mock = MagicMock()

    def test_handle_stream_stop_robot(self):
        # Simulate target center at the center
        self.vsh_mock.get_center.return_value = [480, 100]
        
        # Simulate a lidar scan with an object too close to the robot
        self.lsh_mock.get_scan.return_value = [[60, 80, 110], [90, 100, 70], [120, 120, 115]]

        # Create DecisionMaker instance
        decision_maker = DecisionMaker(self.vsh_mock, self.lsh_mock, self.cs_mock)

        # Create a thread to run _handle_stream with a timeout
        handle_stream_thread = threading.Thread(target=decision_maker._handle_stream)
        handle_stream_thread.start()

        # Wait for a specific duration (e.g., 1 second)
        time.sleep(1)

        # Set the stop_event to break out of the loop
        decision_maker.stop_event.set()

        # Join the thread to ensure it finishes
        handle_stream_thread.join()

        # Check if control data is set to stop the robot
        self.assertEqual(decision_maker.control_data, [0.0, 0.0])

    def test_handle_stream_continue_moving(self):
        # Simulate target center at the center
        self.vsh_mock.get_center.return_value = [480, 100]

        # Simulate a lidar scan with no object too close to the robot
        self.lsh_mock.get_scan.return_value = [[60, 80, 110], [90, 100, 120]]

        # Create DecisionMaker instance
        decision_maker = DecisionMaker(self.vsh_mock, self.lsh_mock, self.cs_mock)

        # Create a thread to run _handle_stream with a timeout
        handle_stream_thread = threading.Thread(target=decision_maker._handle_stream)
        handle_stream_thread.start()

        # Wait for a specific duration (e.g., 1 second)
        time.sleep(1)

        # Set the stop_event to break out of the loop
        decision_maker.stop_event.set()

        # Join the thread to ensure it finishes
        handle_stream_thread.join()
        
        # Check if control data is set to move forward
        self.assertEqual(decision_maker.control_data, [0.0, 0.4])
    
    def test_make_video_decision(self):
        # Create DecisionMaker instance
        decision_maker = DecisionMaker(None, None, None)
        
        # Test when target center is at the right of the center
        target_center_right = [600, 100]
        decision = decision_maker._make_video_decision(target_center_right)
        self.assertEqual(decision, [0.125, 0])

        # Test when target center is at the left of the center
        target_center_left = [300, 100]
        decision = decision_maker._make_video_decision(target_center_left)
        self.assertEqual(decision, [-0.1875, 0])

        # Test when target center is at the center
        target_center_center = [480, 100]
        decision = decision_maker._make_video_decision(target_center_center)
        self.assertEqual(decision, [0.0, 0.4])

        # Test when target center is [0, 0]
        target_center_zero = [0, 0]
        decision = decision_maker._make_video_decision(target_center_zero)
        self.assertIsNone(decision)

    def test_make_lidar_decision(self):
        # Create DecisionMaker instance
        decision_maker = DecisionMaker(None, None, None)

        # Test when lidar scan is empty
        lidar_scan_empty = []
        decision = decision_maker._make_lidar_decision(lidar_scan_empty)
        self.assertFalse(decision)

        # Test when no object is too close to the robot
        lidar_scan_safe = [[60, 80, 110], [90, 100, 120]]
        decision = decision_maker._make_lidar_decision(lidar_scan_safe)
        self.assertFalse(decision)

        # Test when an object is too close to the robot
        lidar_scan_close = [[60, 80, 110], [90, 100, 70], [120, 120, 115]]
        decision = decision_maker._make_lidar_decision(lidar_scan_close)
        self.assertTrue(decision)

if __name__ == '__main__':
    unittest.main()
