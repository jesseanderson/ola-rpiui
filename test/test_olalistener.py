import unittest
from olalistener import UIEvent

class TestUIEvent(unittest.TestCase):
  """Tests the UIEvent class for passing functions to the UI"""

  def setUp(self):
    """Resets testing variables"""
    self._function_executed = False
    self._args = None

  def uievent_function(self, *args):
    """A function that sets testing variables when executed"""
    self._function_executed = True
    self._args = args

  def test_no_args(self):
    """Tests to ensure that when no args are provided, the function provided
       is still executed and the empty tuple is passed in.
    """
    event = UIEvent(self.uievent_function)
    event.run()
    self.assertTrue(self._function_executed)
    self.assertIs(self._args, ())

  def test_args_list(self):
    """Tests to ensure that when args are provided with a function, 
       the function is executed correctly with those args.
    """
    test_args = [1, 'hello', 2]
    event = UIEvent(self.uievent_function, test_args)
    event.run()
    self.assertTrue(self._function_executed)
    self.assertEquals(self._args, (1,'hello',2))

  def test_none_as_input(self):
    """Tests to see that UIEvent accepts None as a function and
       does not fail.
    """
    event = UIEvent(None)
    event.run()
    self.assertFalse(self._function_executed)
    self.assertIsNone(self._args)
