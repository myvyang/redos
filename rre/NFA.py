#!/usr/bin/env python
# coding: utf-8

import threading
from .simple_range import Range

switcher = {
    "RE": ["union", "simple_RE", "simple_RE#union"],
    "simple_RE": ["concatenation", "basic_RE", "basic_RE#concatenation"],
    "union": ["RE", "simple_RE", "simple_RE#union"],
    "concatenation": ["simple_RE", "simple_RE#basic_RE"],
    "basic_RE": ["star", "plus", "question", "num_copy", "elementary_RE"],
    "star": ["elementary_RE"],
    "plus": ["elementary_RE"],
    "question": ["elementary_RE"],
    "num_copy": ["elementary_RE"],
    "elementary_RE": ["group", "any", "eos", "sos", "char", "char_group", "set"],
    "group": ["RE"],
    "any": [],
    "eos": [],
    "sos": [],
    "char": [],
    "char_group": [],
    "set": ["positive_set", "negative_set"],
    "positive_set": ["set_items"],
    "negative_set": ["set_items"],
    "set_items": ["set_item", "set_item#set_items"],
    "set_item": ["range", "char", "char_group"],
    "range": ["char#char"]
}

ENTRY_MARK = "ENTRY"
OUT_MARK = "OUT"

MARK = 0
mark_lock = threading.Lock()
PIN = 0
pin_lock = threading.Lock()
def get_mark():
    global mark_lock, MARK
    mark_lock.acquire()
    MARK += 1
    R = MARK
    mark_lock.release()
    return R

def get_pin():
    global pin_lock, PIN
    pin_lock.acquire()
    PIN -= 1
    R = PIN
    pin_lock.release()
    return R

class Path():
    def __init__(self, target, _range=None):
        self.range = _range
        self.target = target

    def __repr__(self):
        return "-%s--%s" % (self.range, self.target)

class NFA():
    def __init__(self):
        self.entry = get_mark()
        self.out = get_mark()
        self.found_redos = False
        self.build_redos = False
        self.paths = {
            self.entry: [],
            self.out: []
        }

    def add_path(self, _from, _to, _range):
        if _from == ENTRY_MARK:
            _from = self.entry
        if _to == OUT_MARK:
            _to = self.out

        if _from not in self.paths:
            self.paths[_from] = []

        for p in self.paths[_from]:
            if p.target == _to:
                return self
        self.paths[_from].append(Path(_to, _range))
        return self

    def remove_path(self, _from, _to):
        if _from not in self.paths:
            return
        new_paths = []
        for path in self.paths[_from]:
            if path.target != _to:
                new_paths.append(path)
        
        self.paths[_from] = new_paths
        return self

    def combine_path(self, nfa):
        for position in nfa.paths:
            paths = nfa.paths[position]
            for path in paths:
                self.add_path(position, path.target, path.range)

    def union_nfa(self, nfa):
        self.add_path(self.entry, nfa.entry, None)
        self.add_path(nfa.out, self.out, None)
        self.combine_path(nfa)
        return self

    def add_nfa(self, nfa):
        self.add_path(self.entry, nfa.entry, None)
        self.add_path(nfa.out, self.out, None)
        self.combine_path(nfa)                 
        return self

    def concat_nfa(self, nfa):
        self.add_path(self.out, nfa.entry, None)
        self.out = nfa.out
        self.combine_path(nfa)     
        return self

    def add_nfa_star(self, nfa):
        self.add_path(self.entry, nfa.entry, None)
        self.add_path(nfa.out, self.out, None)
        self.add_path(self.entry, self.out, None)
        self.add_path(nfa.out, nfa.entry, None)
        self.combine_path(nfa)
        return self

    def add_nfa_question(self, nfa):
        self.add_nfa(nfa)
        self.add_path(self.entry, self.out, None)
        return self

    def search(self, star_replaces, redos):
        routes = [
            [
                [self.entry],   # position path
                [],             # eating chars
            ]
        ]
        end_routes = []
        while routes:
            route = routes.pop(0)
            positions = route[0]
            chars = route[1]
            position = positions[-1]

            paths = self.paths[position]
            for path in paths:
                if path.target in positions:
                    continue

                if self.found_redos:
                    new_positions = positions+[path.target]
                    if not path.range:
                        if path.target == self.out:
                            return []

                        routes.insert(0, [new_positions, chars])
                        continue
                    else:
                        r = Range.create_full().exclude_range(path.range)
                        if r.set:
                            new_chars = chars + [r.set]
                            self.build_redos = True
                            return [[new_positions, new_chars]]

                if path.target < 0:
                    sub_nfa = star_replaces[path.target]
                    next_paths = self.paths[path.target]
                    next_target = next_paths[0].target
                    assert len(next_paths) == 1
                    assert not next_paths[0].range

                    sub_routes = sub_nfa.search(star_replaces, redos)

                    if redos:
                        out_paths, overlaps = sub_nfa.search_two_path()
                        if len(out_paths) > 1:
                            self.found_redos = True
                            new_chars = chars + overlaps * 40
                            new_positions = positions + [
                                path.target, next_target]

                            if next_target == self.out:
                                return []

                            routes.insert(0, [new_positions, new_chars])
                            continue

                    for sub_route in sub_routes:
                        new_positions = positions + [
                            path.target, next_target]
                        new_chars = chars + sub_route[1]

                        if next_target == self.out:
                            end_routes.append([new_positions, new_chars])
                        else:
                            routes.append([new_positions, new_chars])

                    append_nfa = NFA().add_nfa_star(sub_nfa)
                    path.target = append_nfa.entry
                    append_nfa.add_path(append_nfa.out, next_target, None)
                    self.combine_path(append_nfa)

                else:
                    new_positions = positions+[path.target]
                    new_chars = chars
                    if path.range:
                        new_chars = chars + [path.range.set]

                    if path.target == self.out:
                        end_routes.append([new_positions, new_chars])
                    else:
                        routes.append([new_positions, new_chars])

        return end_routes

    def search_two_path(self):
        def find_stop(position):
            STOP_POSITION = -1

            def _find_stop(position, _prefix_set):
                prefix_set = _prefix_set.copy()
                prefix_set.add(position)
                paths = self.paths[position]
                epsilon_nexts = []
                for path in paths:
                    if not path.range:

                        if path.target in prefix_set:
                            epsilon_nexts.append(
                                [STOP_POSITION]
                            )
                            continue

                        next_nexts = _find_stop(path.target, prefix_set)
                        for n in next_nexts:
                            epsilon_nexts.append(
                                [position] + n
                            )
                    else:
                        epsilon_nexts.append([position])

                return epsilon_nexts
            
            epsilon_nexts = _find_stop(position, set())
            new_en = []
            for n in epsilon_nexts:
                if -1 not in n:
                    new_en.append(n)
            epsilon_nexts = new_en
            return epsilon_nexts

        def advance(epsilon_nexts):
            advance_tasks = [
                [epsilon_nexts, []]
            ]

            def _advance(epsilon_nexts, prefix_overlaps):
                length = len(epsilon_nexts)
                if length > 1:
                    for i in range(length):
                        for j in range(length):
                            if i >= j:
                                continue
                            f1 = epsilon_nexts[i][-1]
                            f2 = epsilon_nexts[j][-1]

                            if f1 == f2:
                                if prefix_overlaps:
                                    out_paths = [epsilon_nexts[i], epsilon_nexts[j]]
                                    return out_paths, prefix_overlaps

                            paths1 = self.paths[f1]
                            paths2 = self.paths[f2]
                            for p1 in paths1:
                                for p2 in paths2:
                                    range1 = p1.range
                                    range2 = p2.range

                                    if not range1 or not range2:
                                        continue

                                    overlap = range1.set & range2.set
                                    if overlap:
                                        n1 = find_stop(p1.target)
                                        n2 = find_stop(p2.target)
                                        new_en1 = epsilon_nexts[i] + [p1.target]
                                        new_en2 = epsilon_nexts[j] + [p2.target]                               
                                        full_n = []
                                        for n in n1:
                                            full_n.append(new_en1 + n)
                                        for n in n2:
                                            full_n.append(new_en2 + n)
                                        advance_tasks.append([full_n, prefix_overlaps + [overlap]])

                for en in epsilon_nexts:
                    paths = self.paths[en[-1]]
                    for path in paths:
                        if not path.range:
                            continue
                        _set = path.range.set
                        ns = find_stop(path.target)
                        full_n = []
                        for n in ns:
                            full_n.append(en + [path.target] + n)

                        advance_tasks.append([full_n, prefix_overlaps + [_set]])
                    

                return [], []

            i = 0
            while i < len(advance_tasks) and i < 2000:
                e, p = advance_tasks[i]
                out_paths, overlaps = _advance(e, p)                
                if len(out_paths) > 1:
                    print("search path from redos: %s" % i)
                    return out_paths, overlaps

                i += 1

            return [], []

        self.add_path(self.out, self.entry, None)
        epsilon_nexts = find_stop(self.entry)
        out_paths, overlaps = advance(epsilon_nexts)
        self.remove_path(self.out, self.entry)

        return out_paths, overlaps

def compute_char_group_range(value):
    _range = Range.create_null()
    if value == r"\s":
        for c in "\n\r\t\f":
            _range.add_one(ord(c))
    elif value == r"\S":
        _range = Range.create_full()
        for c in "\n\r\t\f":
            _range.exclude(ord(c), ord(c))
    elif value == r"\w":
        _range.add(ord("a"), ord("z"))
        _range.add(ord("A"), ord("Z"))
        _range.add(ord("0"), ord("9"))
        _range.add_one(ord("_"))
    elif value == r"\W":
        _range = Range.create_full()
        _range.exclude(ord("a"), ord("z"))
        _range.exclude(ord("A"), ord("Z"))
        _range.exclude(ord("0"), ord("9"))
        _range.exclude(ord("_"), ord("_"))
    return _range

def char_range(char_seq):
    assert char_seq[0] == "char"
    # content_type = content[0][0]

    assert char_seq[1][0] == "literal"
    value = char_seq[1][1]
    return NFA().add_path(ENTRY_MARK, OUT_MARK, Range(ord(value), ord(value)))

def compute_set_range(seq):
    if seq[0] == "positive_set":
        assert len(seq) > 2
        assert seq[2][0] == "set_items"
        return compute_set_range(seq[2])
    if seq[0] == "negative_set":
        assert len(seq) > 2
        assert seq[2][0] == "set_items"
        _sub_range = compute_set_range(seq[2])
        return Range.create_full().exclude_range(_sub_range)
    if seq[0] == "set_items":
        assert len(seq) > 1
        _sub1 = compute_set_range(seq[1])
        if len(seq) == 2:
            return _sub1
        _sub2 = compute_set_range(seq[2])
        return _sub1.combine(_sub2)
    if seq[0] == "set_item":
        assert seq[0] == "set_item"
        assert len(seq) == 2
        if seq[1][0] == "char":
            value = seq[1][1][1]
            return Range(ord(value), ord(value))
        elif seq[1][0] == "char_group":
            value = seq[1][1][1]
            return compute_char_group_range(value)
        elif seq[1][0] == "range":
            assert seq[1][0] == "range"
            _from = seq[1][1][1][1]
            _to = seq[1][3][1][1]
            return Range(ord(_from), ord(_to))

    raise Exception("never reach")    

def remap(nfa):
    m = {}
    m[nfa.entry] = get_mark()
    m[nfa.out] = get_mark()
    new_nfa = NFA()
    new_nfa.entry = m[nfa.entry]
    new_nfa.out = m[nfa.out]
    for position in nfa.paths:
        paths = nfa.paths[position]

        if position not in m:
            m[position] = get_mark()
        for path in paths:
            if path.target not in m:
                m[path.target] = get_mark()
            new_nfa.add_path(m[position], m[path.target], path.range)

    return new_nfa

def nfa_build(seq):
    star_replaces = {}

    def _nfa_build(seq):
        name = seq[0]
        content = seq[1:]

        if name == "char_group":
            assert seq[1][0] == "literal"
            value = seq[1][1]
            return NFA().add_path(ENTRY_MARK, OUT_MARK, compute_char_group_range(value))

        if name == "char":
            # content_type = content[0][0]
            assert seq[1][0] == "literal"
            value = seq[1][1]
            return NFA().add_path(ENTRY_MARK, OUT_MARK, Range(ord(value), ord(value)))

        if name == "set":
            assert len(content) == 1
            _range = compute_set_range(content[0])
            return NFA().add_path(ENTRY_MARK, OUT_MARK, _range)

        valid = []
        for item in content:
            if item[0] in switcher:
                valid.append(item)

        sub_type = "#".join([item[0] for item in valid])
        if valid:
            children = switcher[name]
            if sub_type not in children:
                raise Exception("%s not in %s" % (sub_type, name))

        sub_nfas = []
        for item in valid:
            sub_nfa = _nfa_build(item)
            sub_nfas.append(sub_nfa)

        if name == "star":
            assert len(sub_nfas) == 1
            pin = get_pin()

            nfa = NFA()
            nfa.entry = pin
            nfa.add_path(ENTRY_MARK, OUT_MARK, None)

            star_replaces[pin] = sub_nfas[0]

            return nfa
                
        if name == "plus":
            assert len(sub_nfas) == 1
            nfa = NFA().add_nfa(remap(sub_nfas[0]))
            pin = get_pin()

            new_nfa = NFA()
            new_nfa.entry = pin
            new_nfa.add_path(ENTRY_MARK, OUT_MARK, None)
            nfa.concat_nfa(new_nfa)

            star_replaces[pin] = sub_nfas[0]

            return nfa

        if name == "question":
            assert len(sub_nfas) == 1
            sub_nfa = sub_nfas[0]
            return NFA().add_nfa_question(sub_nfa)

        if name == "num_copy":
            assert len(sub_nfas) == 1
            assert len(seq) == 3
            assert seq[2][0] == "num_copy_struct"

            num = seq[2][1][1]
            # num_top = num
            # if len(seq[2]) == 3:
            #     num_top = seq[2][2][1]
            # more_num = num_top - num

            sub_nfa = sub_nfas[0]
            nfa = NFA()
            nfa.add_path(ENTRY_MARK, OUT_MARK, None)
            for _ in range(num):
                new_nfa = NFA().add_nfa(remap(sub_nfa))
                nfa = nfa.concat_nfa(new_nfa)
            return nfa
            """
            if more_num > 10:
                new_nfa = NFA().add_nfa_star(remap(sub_nfa))
                nfa = nfa.concat_nfa(new_nfa)
            else:
                for _ in range(more_num):
                    new_nfa = NFA().add_nfa_question(remap(sub_nfa))
                    nfa = nfa.concat_nfa(new_nfa)
            return nfa
            """

        if name in ["eos", "sos"]:
            return NFA().add_path(ENTRY_MARK, OUT_MARK, None)

        if name == "any":
            _range = Range.create_full()
            return NFA().add_path(ENTRY_MARK, OUT_MARK, _range)

        assert sub_nfas
        assert len(sub_nfas) < 3

        if len(sub_nfas) == 2:
            second_sub_name = valid[1][0]
            if second_sub_name == "union":
                return sub_nfas[0].union_nfa(sub_nfas[1])
            if second_sub_name == "concatenation":
                return sub_nfas[0].concat_nfa(sub_nfas[1])
            if second_sub_name == "basic_RE":
                raise Exception("never reach: %s" % sub_type)
                # return sub_nfas[0].concat_nfa(sub_nfas[1])
            raise Exception("never reach: %s" % sub_type)        

        return sub_nfas[0]
    
    nfa = _nfa_build(seq)
    nfa = NFA().add_nfa(nfa)
    return nfa, star_replaces
