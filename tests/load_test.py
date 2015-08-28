from faunadb.objects import Ref
from nose.tools import nottest

from test_case import FaunaTestCase

class LoadTest(FaunaTestCase):
  def setUp(self):
    super(LoadTest, self).setUp()

    self.client.post("classes", {"name": "widgets"})
    # Must create the index or CPU load will go back down when test is over.
    self.client.post("indexes", {
      "name": "widgets_by_n",
      "source": Ref("classes", "widgets"),
      "path": "data.n"
    })
    # Don't even have to create any instances.

  # Enabling this this causes high CPU usage!
  @nottest
  def test_lots_of_tests(self):
    for x in range(100):
      self.tearDown() # destroy the db
      self.setUp() # create the db and a class and index
