import unittest
from run import Spider, run, analyze


class TestSpider(unittest.TestCase):

  def setUp(self):
      self.spider = Spider()

  def tearDown(self):
      pass

  def test_basic(self):
      self.spider.feed('<p><a href="asdf">qwer</a></p>')
      self.assertEqual(self.spider.next_link, 'asdf')

  def test_italic(self):
      self.spider.feed('<p><i>testing stuff<a href="asdf">qwer</a></i></p>')
      self.assertEqual(self.spider.next_link, None)

  def test_parens(self):
      self.spider.feed('<p>testing stuff (<a href="asdf">qwer</a>)</p>')
      self.assertEqual(self.spider.next_link, None)

  def test_bad_links(self):
      self.spider.feed('<p>testing stuff (<a href="wikimedia/asdf">qwer</a>)</p>')
      self.assertEqual(self.spider.next_link, None)

  def test_bad_links2(self):
      self.spider.feed('<p>testing stuff (<a href="#asdf">qwer</a>)</p>')
      self.assertEqual(self.spider.next_link, None)



if __name__ == '__main__':
    unittest.main()
