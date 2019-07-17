#!/usr/bin/env python
# coding: utf-8

import pprint
from .laucha import get_sequence
from .NFA import nfa_build

def print_seq(seq):
    pprint.pprint(seq)

def printable():
    return "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"

def choose_char(s):
    s1 = set(s)
    s2 = set([ord(x) for x in printable()])
    s = s1 & s2
    if s:
        return s.pop()
    return s1.pop()

def process(seq, redos):
    """
        seq: name, sub_seq...
    """
    nfa, star_replaces = nfa_build(seq)
    routes = nfa.search(star_replaces, redos)

    if redos and not nfa.build_redos:
        return False, ""

    if routes:
        chars = routes[0][1]
        matches = ""
        for _range in chars:
            c = chr(choose_char(_range) )
            if c not in printable():
                c = "\\" + str(ord(c))
            matches += c
        return True, matches
    return False, ""

def find_redos(regex):
    nr = regex
    if nr[-1] == "$":
        nr[-1] == "h"
    has_redos, matches = process(get_sequence(nr), True)
    return has_redos, matches

def find_match(regex):
    has_match, matched = process(get_sequence(regex), False)
    return has_match, matched
