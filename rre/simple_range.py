#!/usr/bin/env python
# coding: utf-8

class Range():
    """
    range 0 to 255.
    """

    def __init__(self, a, b):
        """
            a-b, contains a,b
        """
        self.set = set()
        self.add(a, b)

    @staticmethod
    def create_full():
        return Range(0, 255)
    
    @staticmethod
    def create_null():
        _range = Range(0, 0)
        _range.exclude(0, 0)
        return _range

    def add(self, a, b):
        for i in range(a, b+1):
            self.set.add(i)
        return self

    def add_one(self, a):
        self.set.add(a)
        return self

    def exclude(self, a, b):
        for i in range(a, b+1):
            if i in self.set:
                self.set.remove(i)
        return self

    def combine(self, range2):
        self.set |= range2.set
        return self

    def exclude_range(self, range2):
        for i in range2.set:
            if i in self.set:
                self.set.remove(i)
        return self

    def __repr__(self):
        return str(self.set)