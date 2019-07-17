#!/usr/bin/env python
# coding: utf-8

import os
import sys

"""
laucha: regular expressions static compiler.
Alejandro Santos, @alejolp
"""

RE_SPECIAL_SYMBOLS = set(".[]^$()*+?|{}")
RE_CLASSES = ['[:upper:]', '[:lower:]', '[:alpha:]', '[:alnum:]', '[:digit:]', '[:xdigit:]', '[:punct:]', '[:blank:]', '[:space:]', '[:cntrl:]', '[:graph:]', '[:print:]']

TOK_SPECIAL = 'special'
TOK_LITERAL = 'literal'
TOK_CLASS = 'class'
TOK_ENDOFSTR = 'eos'

class laucha_parser_error(Exception):
    pass

class laucha_parser_missing_token(Exception):
    """
    Backtrack the parser
    """
    pass

def tokenize_regexp(S):
    i = 0
    R = []
    in_char_class = False
    try:
        while i < len(S):
            if S.startswith('[:', i):
                class_str = None
                for c in RE_CLASSES:
                    if S.startswith(c, i):
                        class_str = c
                        break
                if class_str is None:
                    raise laucha_parser_error()
                R.append((TOK_CLASS, class_str))
                i += len(class_str)
            elif S.startswith('[^', i):
                R.append((TOK_SPECIAL, S[i:i+2]))
                i = i + 2
            elif S[i] in RE_SPECIAL_SYMBOLS:
                if in_char_class and S[i] not in "^-]\\":
                    R.append((TOK_LITERAL, S[i]))
                else:
                    R.append((TOK_SPECIAL, S[i]))

                if S[i] == '[':
                    in_char_class = True
                if S[i] == ']':
                    in_char_class = False                
                i = i + 1
            elif S[i] == '\\':
                i = i + 1
                if S[i] in "sSwW":
                    R.append((TOK_LITERAL, "\\" + S[i]))
                elif S[i] in "nrtf":
                    m = {"n": "\n", "r": "\r", "t": "\t", "f": "\f"}
                    R.append((TOK_LITERAL, m[S[i]]))
                else:
                    R.append((TOK_LITERAL, S[i]))
                i = i + 1
            else:
                R.append((TOK_LITERAL, S[i]))
                i = i + 1
    except Exception as e:
        raise laucha_parser_error("Exception: " + str(e))
    R.append((TOK_ENDOFSTR, None))
    return R

class regexp_node:
    def __init__(self, name):
        self.name = name
        self.childs = []

    def __repr__(self):
        return "('" + self.name + "', " + ', '.join([repr(x) for x in self.childs]) + ")"

class regexp_parser:
    """
    Recursive descent parser for regular expressions.

    GRAMMAR
    -------

    http://www.cs.sfu.ca/~cameron/Teaching/384/99-3/regexp-plg.html

    <START>             ::= <RE> <TOK_ENDOFSTR>
    <RE>                ::= <union> | <simple_RE>
    <union>             ::= <RE> "|" <simple_RE>
    <simple_RE>         ::= <concatenation> | <basic_RE>
    <concatenation>     ::= <simple_RE> <basic_RE>
    <basic_RE>          ::= <star> | <plus> | <question> | <num_copy> | <elementary_RE>
    <star>              ::= <elementary_RE> "*"
    <plus>              ::= <elementary_RE> "+"
    <question>          ::= <elementary_RE> "?"
    <num_copy>          ::= <elementary_RE> <num_copy_struct>
    <num_copy_struct>   ::= "{" num "}" | "{" num "," num "}"
    <num>               ::= 0123456789
    <elementary_RE>     ::= <group> | <any> | <eos> | <sos> | <char> | <char_group> | <set>
    <group>             ::= "(" <RE> ")"
    <set>               ::= <positive_set> | <negative_set>
    <positive_set>      ::= "[" <set_items> "]"
    <negative_set>      ::= "[^" <set_items> "]"
    <set_items>         ::= <set_item> | <set_item> <set_items>
    <set_item>          ::= <range> | <char> | <char_group>
    <range>             ::= <char> "-" <char>
    <any>               ::= "."
    <sos>               ::= "^"
    <eos>               ::= "$"
    <char>              ::= any non metacharacter | "\" metacharacter
    <char_group>         ::= "\s" | "\w" | \S | \W

    # Left factored grammar 

    <RE>                ::= <simple_RE> <union> | <simple_RE>
    <union>             ::= "|" <simple_RE> <union> | "|" <simple_RE>
    <simple_RE>         ::= <basic_RE> <concatenation> | <basic_RE>
    <concatenation>     ::= <simple_RE>

    """
    def __init__(self, T):
        self.toks = T
        self.pos = 0

    def tok_peek(self):
        t = self.toks[self.pos]
        #print "peek", t
        return t

    def tok_next(self):
        t = self.toks[self.pos]
        #print "next", t
        self.pos += 1
        return t

    def parse_any(self):
        """
        <any>               ::= "."
        """
        if self.tok_peek() != (TOK_SPECIAL, '.'):
            raise laucha_parser_missing_token()
        node = regexp_node('any')
        node.childs.append(self.tok_next())
        return node

    def parse_sos(self):
        """
        <sos>               ::= "^"
        """
        if self.tok_peek() != (TOK_SPECIAL, '^'):
            raise laucha_parser_missing_token()
        node = regexp_node('sos')
        node.childs.append(self.tok_next())
        return node

    def parse_eos(self):
        """
        <eos>               ::= "$"
        """
        if self.tok_peek() != (TOK_SPECIAL, '$'):
            raise laucha_parser_missing_token()
        node = regexp_node('eos')
        node.childs.append(self.tok_next())
        return node

    def parse_char(self):
        """
        <char>              ::= any non metacharacter | "\" metacharacter
        """
        if self.tok_peek()[0] != TOK_LITERAL:
            raise laucha_parser_missing_token()

        if self.tok_peek()[1] in "\s\w\S\W":
            node = regexp_node('char_group')
            node.childs.append(self.tok_next())
        else:
            node = regexp_node('char')
            node.childs.append(self.tok_next())
        return node

    def parse_range(self):
        """
        <range>             ::= <char> "-" <char>
        """
        oldpos = self.pos
        try:
            a = self.parse_char()
            if self.tok_peek()[1] != '-':
                raise laucha_parser_missing_token()
            b = self.tok_next()
            c = self.parse_char()
            node = regexp_node('range')
            node.childs.append(a)
            node.childs.append(b)
            node.childs.append(c)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_set_item(self):
        """
        <set_item>          ::= <range> | <char>
        """
        oldpos = self.pos
        try:
            node = regexp_node('set_item')

            try:
                a = self.parse_range()
                node.childs.append(a)
                return node            
            except laucha_parser_missing_token as e:
                pass

            a = self.parse_char()
            node.childs.append(a)

            return node            
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_set_items(self):
        """
        <set_items>         ::= <set_item> | <set_item> <set_items>
        """
        oldpos = self.pos
        try:
            node = regexp_node('set_items')

            a = self.parse_set_item()
            node.childs.append(a)

            try:
                b = self.parse_set_items()
                node.childs.append(b)
            except laucha_parser_missing_token as e:
                pass

            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_set(self):
        """
        <set>               ::= <positive_set> | <negative_set>
        """
        oldpos = self.pos
        try:
            node = regexp_node('set')

            try:
                a = self.parse_positive_set()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                pass

            a = self.parse_negative_set()
            node.childs.append(a)

            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_positive_set(self):
        """
        <positive_set>      ::= "[" <set_items> "]"
        """
        oldpos = self.pos
        try:
            node = regexp_node('positive_set')
            if self.tok_peek() != (TOK_SPECIAL, '['):
                raise laucha_parser_missing_token()

            a = self.tok_next()
            b = self.parse_set_items()
            if self.tok_peek() != (TOK_SPECIAL, ']'):
                raise laucha_parser_missing_token()

            c = self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            node.childs.append(c)            
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_negative_set(self):
        """
        <negative_set>      ::= "[^" <set_items> "]"
        """
        oldpos = self.pos
        try:
            node = regexp_node('negative_set')
            if self.tok_peek() != (TOK_SPECIAL, '[^'):
                raise laucha_parser_missing_token()
            a = self.tok_next()
            b = self.parse_set_items()
            if self.tok_peek() != (TOK_SPECIAL, ']'):
                raise laucha_parser_missing_token()
            c = self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            node.childs.append(c)            
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_group(self):
        """
        <group>             ::= "(" <RE> ")"
        """
        oldpos = self.pos
        try:
            node = regexp_node('group')
            if self.tok_peek() != (TOK_SPECIAL, '('):
                raise laucha_parser_missing_token()
            a = self.tok_next()
            if self.tok_peek() == (TOK_SPECIAL, '?'):
                self.tok_next()
            b = self.parse_RE()
            if self.tok_peek() != (TOK_SPECIAL, ')'):
                raise laucha_parser_missing_token()
            c = self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            node.childs.append(c)            
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_START(self):
        """
            <START>             ::= <RE> <TOK_ENDOFSTR>
        """
        oldpos = self.pos
        try:
            node = regexp_node('RE')
            a = self.parse_RE()
            if self.tok_peek() != (TOK_ENDOFSTR, None):
                raise laucha_parser_missing_token()
            b = self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_RE(self):
        """
        <RE>                ::= <simple_RE> <union> | <simple_RE>
        """
        oldpos = self.pos
        try:
            node = regexp_node('RE')

            a = self.parse_simple_RE()
            node.childs.append(a)

            try:
                b = self.parse_union()
                node.childs.append(b)
            except laucha_parser_missing_token as e:
                pass

            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise
        
    def parse_union(self):
        """
        <union>             ::= "|" <simple_RE> <union> | "|" <simple_RE>
        """
        oldpos = self.pos
        try:
            node = regexp_node('union')

            if self.tok_peek() != (TOK_SPECIAL, '|'):
                raise laucha_parser_missing_token()
            a = self.tok_next()
            node.childs.append(a)
            
            b = self.parse_simple_RE()
            node.childs.append(b)

            try:
                c = self.parse_union()
                node.childs.append(c)
            except laucha_parser_missing_token as e:
                pass

            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise
        
    def parse_simple_RE(self):
        """
        <simple_RE>         ::= <basic_RE> <concatenation> | <basic_RE>
        """
        oldpos = self.pos
        try:
            node = regexp_node('simple_RE')
            a = self.parse_basic_RE()
            node.childs.append(a)

            try:
                b = self.parse_concatenation()
                node.childs.append(b)
            except laucha_parser_missing_token as e:
                pass

            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise
        
    def parse_concatenation(self):
        """
        <concatenation>     ::= <simple_RE>
        """
        oldpos = self.pos
        try:
            node = regexp_node('concatenation')
            a = self.parse_simple_RE()
            node.childs.append(a)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_basic_RE(self):
        """
        <basic_RE>          ::= <star> | <plus> | <question> | <num_copy> | <elementary_RE>
        """
        oldpos = self.pos
        try:
            node = regexp_node('basic_RE')
            try:
                a = self.parse_star()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_plus()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_question()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_num_copy()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            a = self.parse_elementary_RE()
            node.childs.append(a)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_star(self):
        """
        <star>              ::= <elementary_RE> "*"
        """
        oldpos = self.pos
        try:
            node = regexp_node('star')
            a = self.parse_elementary_RE()
            if self.tok_peek() != (TOK_SPECIAL, '*'):
                raise laucha_parser_missing_token()
            b = self.tok_next()
            if self.tok_peek() == (TOK_SPECIAL, '?'):
                self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_plus(self):
        """
        <plus>              ::= <elementary_RE> "+"
        """
        oldpos = self.pos
        try:
            node = regexp_node('plus')
            a = self.parse_elementary_RE()
            if self.tok_peek() != (TOK_SPECIAL, '+'):
                raise laucha_parser_missing_token()
            b = self.tok_next()
            if self.tok_peek() == (TOK_SPECIAL, '?'):
                self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_question(self):
        """
        <question>          ::= <elementary_RE> "?"
        """
        oldpos = self.pos
        try:
            node = regexp_node('question')
            a = self.parse_elementary_RE()
            if self.tok_peek() != (TOK_SPECIAL, '?'):
                raise laucha_parser_missing_token()
            b = self.tok_next()
            if self.tok_peek() == (TOK_SPECIAL, '?'):
                self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_num(self):
        """
        <num>               ::= 0123456789
        """
        node = regexp_node('num')
        if self.tok_peek()[1] not in "0123456789":
            raise laucha_parser_missing_token()
        count = 0
        while self.tok_peek()[1] in "0123456789":
            count = int(self.tok_peek()[1]) + count*10
            self.tok_next()
        node.childs.append(count)
        return node

    def parse_num_copy_struct(self):
        """
        <num_copy_struct>   ::= "{" num "}" | "{" num "," num "}"
        """
        oldpos = self.pos
        try:
            node = regexp_node('num_copy_struct')
            if self.tok_peek() != (TOK_SPECIAL, '{'):
                raise laucha_parser_missing_token()
            self.tok_next()
            a = self.parse_num()
            node.childs.append(a)
            if self.tok_peek()[1] == ",":
                self.tok_next()
                b = self.parse_num()
                node.childs.append(b)
                if b.childs[0] < a.childs[0]:
                    raise Exception("in {m,n}, need m <= n")
            if self.tok_peek() != (TOK_SPECIAL, '}'):
                raise laucha_parser_missing_token()
            self.tok_next()
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise        

    def parse_num_copy(self):
        """
        <num_copy>          ::= <elementary_RE> <num_copy_struct>
        """
        oldpos = self.pos
        try:
            node = regexp_node('num_copy')
            a = self.parse_elementary_RE()
            b = self.parse_num_copy_struct()
            if self.tok_peek() == (TOK_SPECIAL, '?'):
                self.tok_next()
            node.childs.append(a)
            node.childs.append(b)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

    def parse_elementary_RE(self):
        """
        <elementary_RE>     ::= <group> | <any> | <eos> | <char> | <set>
        """
        oldpos = self.pos
        try:
            node = regexp_node('elementary_RE')

            try:
                a = self.parse_group()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_any()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_sos()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_eos()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            try:
                a = self.parse_char()
                node.childs.append(a)
                return node
            except laucha_parser_missing_token as e:
                self.pos = oldpos

            a = self.parse_set()
            node.childs.append(a)
            return node
        except laucha_parser_missing_token as e:
            self.pos = oldpos
            raise

def parse_regexp(T):
    p = regexp_parser(T)
    return p.parse_START()

def get_sequence(s):
    return eval(repr(parse_regexp(tokenize_regexp(s))))[1]

def test(S):
    import pprint
    print()
    print(S)

    T = tokenize_regexp(S)
    pprint.pprint(T)

    P = parse_regexp(T)
    pprint.pprint(eval(repr(P)))

def main():
    #test("a\.(\(|\))")

    sys.setrecursionlimit(1000000)

#    test("[a-bcd-e]")
#    test("[a-bd-ec]")
#    test("[^a-b]")

    #test(r"([\sa]|\S)+")
    test(r"(a{3,7}?)+")

    # test("(a|b)*aab")
    # test("(a|b|c|d|e)*aab")
    # test("([cC]at)|([dD]og)")

    #test("[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}")

if __name__ == '__main__':
    main()

