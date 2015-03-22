#!/usr/bin/env python

import sys, os, unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import equivalence

urls = [
    'http://python.org/',           #0
    'http://www.python.org/',       #1
    'www.python.org/index.html',    #2

    'http://www.foobar.com/docs/',  #3

    'www.foobar.com/index.html',    #4
    'http://foobar.com/index.php',  #5
]

unknown_url = 'bogus'

#============ Equivalence test =================================================

class TestEquivalence(unittest.TestCase):
    cls = equivalence.Equivalence

    def setUp(self):
        self.eq = self.cls()
        self.eq.merge(urls[0], urls[1])
        self.eq.merge(urls[1], urls[2])
        self.eq.merge(urls[4], urls[5])
        self.eq.update(urls[3])

    def test_are_equivalent(self):
        self.assert_(self.eq.are_equivalent(urls[0], urls[2]))
        self.assertFalse(self.eq.are_equivalent(urls[0], urls[4]))
        self.assert_(self.eq.are_equivalent(unknown_url, unknown_url))

    def test_partition(self):
        self.assertEqual(self.eq.partition(urls[0]), set(urls[:3]))
        self.assertEqual(self.eq.partition(urls[5]), set(urls[4:]))
        # the partition of an unknown object is the empty set()
        self.assertEqual(self.eq.partition('www.unknown.com'), set())

    def test_partitions_with_arg(self):
        self.assertEqualIgnoringOrder(self.eq.partitions(urls[1:5]),
                          [urls[1:3], urls[3:4], urls[4:5]])
        # duplicates in the original arg are preserved
        self.assertEqualIgnoringOrder(self.eq.partitions(2*urls[1:5]),
                          [2*urls[1:3], 2*urls[3:4], 2*urls[4:5]])

    def test_partitions_no_arg(self):
        # before update
        self.assertEqualIgnoringOrder(self.eq.partitions(),
                                      [urls[0:3], urls[3:4], urls[4:]])
        # after update
        self.eq.update(unknown_url)
        self.assertEqualIgnoringOrder(self.eq.partitions(),
                                      [urls[0:3], urls[3:4], urls[4:], [unknown_url]])

    def test_multimerge(self):
        # merge urls[:2] with urls[4:]
        self.eq.merge(urls[2], urls[5])
        self.assertEqualIgnoringOrder(self.eq.partitions(urls),
                          [urls[:3]+urls[4:], [urls[3]]])
        self.assertEqual(self.eq.partition(urls[5]), set(urls[:3]+urls[4:]))
        self.assert_(self.eq.are_equivalent(urls[4], urls[1], urls[0]))
        self.assertEqual(self.eq.partition(unknown_url), set())
        # merge all
        self.eq.merge(urls[3], urls[0])
        self.assertEqualIgnoringOrder(self.eq.partitions(urls), [urls])

    def assertEqualIgnoringOrder(self, partitions1, partitions2):
        # can't use set() because a partition may contain duplicates
        self.assertEqual(sorted(map(sorted,partitions1)),
                         sorted(map(sorted,partitions2)))


#============ KeyEquivalence test ==============================================

import re
# remove protocol, leading 'www' and trailing '/index.$ext'
def normalize(url, _norm_pattern = re.compile(r'''^
                           (?: https?://)?
                           (?: www\.)?
                           (.+?)
                           (?: /index\. (?: s?html? | php | aspx? | jsp) )?
                           $''', re.VERBOSE | re.IGNORECASE)):
    return _norm_pattern.sub(r'\1', url.strip().lower()).rstrip('/')


class TestKeyEquivalence(TestEquivalence):
    cls = equivalence.KeyEquivalence

    def setUp(self):
        self.eq = self.cls(normalize)
        self.eq.update(*urls)
        # implied partitions through normalize() are the same with superclass:
        # [urls[:2], urls[3:4], urls[4:]]


#============ Bidirectional equivalence tests ==================================

class TestBidirectionalEquivalence(TestEquivalence):
    cls = equivalence.BidirectionalEquivalence

class TestKeyBidirectionalEquivalence(TestKeyEquivalence):
    cls = equivalence.KeyBidirectionalEquivalence


if __name__ == '__main__':
    unittest.main()
