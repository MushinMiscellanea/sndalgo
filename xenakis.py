#!/usr/bin/env python3

"""
the iannis xenakis sieve library. or at least just the gist of it.

nov 2019

xenakis.py
==========

this should contain a good amount of utilities all packaged into a neat
little library file. i would like to avoid dependencies. it would be cool
to create an extension api.

quick overview
--------------

essentially i want to have one object I can keep sieveing with freeform,
that keeps track of residuals and assists in doing more complex logic with
them.

further reading
---------------

this is meant to be a reimplementation of
[this article](https://www.mitpressjournals.org/doi/pdf/10.1162/0148926054094396).

set theory, the python data model, functional programming, and an idea of
computer science concepts like modulus are also good to know.
"""

__author__ = 'John Harrington'
__version__ = '0.0.1'


def clean_sieve_str(res: str) -> str:
    """
    removes all whitespace.

    @param res: the residual string.
    @returns the cleaned string.
    """

    res = ''.join(_ for _ in res.strip() if _ != ' ' and _ != '\n')
    return res


def parse_residual(res: str) -> tuple:
    """
    parses a residual--the subunit of a sieve.

    @param res: the residual string.
    @returns tuple representing (modulus, shift, is_negative)
    """

    res = clean_sieve_str(res)

    if res[0] == '!':
        neg = True
        res = res[1:]
    else:
        neg = False

    if '@' in res:
        modulus, shift = (int(_) for _ in res.split('@'))
    else:
        modulus, shift = int(res), 0

    return (modulus, shift, neg)


def parse_sieve_str(res: str) -> list:
    """
    converts a sieve string into an array of compound sieve(s).

    @param res: input residual string.
    @returns a list of a list of tuples
    """

    res = clean_sieve_str(res)
    groups = []

    if '|' in res:
        for group in res.split('|'):
            groups += [parse_sieve_str(group)]

        return groups

    if '&' in res:
        for residual in res.split('&'):
            groups += [parse_residual(residual)]

        return groups

    groups.append([parse_residual(res)])

    return groups


def in_residual(v: int, res: tuple) -> bool:
    """
    checks to see if a value is valid for a residual.

    @param v: the value to check against the residual.
    @param res: the input residual.
    @returns whether the input is valid for the residual.
    """

    mod, shift, neg = res

    if mod == 1 or mod == 0:
        return not neg

    truth = (v - shift) % mod == 0
    return not truth if neg else truth


def for_iter(res: tuple, z: list) -> list:
    """
    returns a filtered iterable against a residual.

    @param res: the residual
    @param z: the iterable
    @returns the filtered iterable
    """

    return list(n for n in z if in_residual(n, res))


def norm_residual(res: tuple) -> tuple:
    """
    returns a normalized residual, with the shift being modulused by the
    modulus.

    @param res: residual
    @returns normalized residual
    """

    return (res[0], res[1] % res[0], res[2])


def simplify_group(group: list) -> list:
    """
    simplifies a group--which are all &--into a single residual.

    @param group: the input group
    @returns a new, single-element list with a simplified residual
    """

    if len(group) == 1:
        # print(f'len_1: {group}')

        return group

    if len(group) == 2:
        m = group[0][0] * group[1][0]
        s = min([group[0][1], group[1][1]])
        r = (m, s, False)
        # print(f'len_2: {m} {s} {r}')

        seek = 0

        while not (
            in_residual(
                s,
                r) == in_residual(
                s,
                group[0]) == in_residual(
                s,
                group[1])) and seek <= m:
            s += 1
            r = (m, s, False)
            seek += 1

        if seek == m:
            raise ValueError(
                'this combination of residuals have no true values.')

        return [r]

    while len(group) >= 2:
        end = group[2:]
        simple = simplify_group(group[:2]) + end
        # print(f"len_3+: {group} {end} {simple}")
        group = simple

    return group


class Sieve:
    """
    the xenakis sieve, all-in-one class.
    """

    _fmt: str = 'set'

    def __init__(self, m=1, s=None, n=None, r=None, fmt=None):
        """
        initializes the sieve.

        * if m is a string, it will be parsed.
        * if m is an int, it will also look for s and n, to create a simple sieve.
        * if m is a sieve, it will be copied.

        @param m: the modulus, string, or sieve.
        @param s: the shift (or 0) for int input.
        @param n: if the sieve is negative or not for int input.
        @param r: residuals (deprecated/under consideration).
        @param fmt: the default output format.
        """

        loaded = False

        if fmt:
            self.fmt = fmt

        if isinstance(m, str):
            residuals = parse_sieve_str(m)

            self._residuals = residuals

            loaded = True

        if isinstance(m, int):
            self._residuals = [[(m, s or 0, n or False)]]

            loaded = True

        if isinstance(m, Sieve):
            self._residuals = m._residuals[:]

            loaded = True

        if not loaded:
            raise ValueError(
                f'the "m" argument is not of types `str`, `int`, or `Sieve`')

        for idx, group in enumerate(self._residuals):
            for jdx, residual in enumerate(group):
                self._residuals[idx][jdx] = norm_residual(residual)

        self._cur_group = 'last'

    @property
    def fmt(self) -> str:
        """
        format type as a string.

        can only be:

        * 'set'     as a set of valid numbers
        * 'unit'    as a unit of relative maginitude based on the z
        * 'bin'     as a full list of the range, with either 1 or 0 denoting
                    each's validity
        * 'delta'   as a list of differences between each valid value (n - 1)
        """

        return self._fmt

    @fmt.setter
    def fmt(self, new: str):
        """
        sets the format type for the sieve.

        @param new: the new format.
        """

        if new in ['set', 'unit', 'bin', 'delta']:
            self._fmt = new
        else:
            print(
                f'[warn] `{new}` is not a possible option for Sieve.fmt; no changes made')

    @property
    def stype(self) -> str:
        """
        returns the complexity of the sieve as a string. possible:

        * simple
        * compound
        * complex
        """

        if len(self._residuals) > 1:
            return 'complex'
        elif len(self._residuals) == 1 and len(self._residuals[0]) > 1:
            return 'compound'
        else:
            return 'simple'

    @property
    def simplified(self) -> str:
        """
        returns a simplified sieve.
        """

        sieves = [
            Sieve(f'{x}@{y}') for x, y, _ in [
                simplify_group(group)[0] for group in self._residuals]]
        simple = sieves[0]
        for sieve in sieves[1:]:
            simple = simple | sieve

        return simple

    def __str__(self) -> str:
        """
        the string representation of this sieve.
        """

        string = []

        for group in self._residuals:
            string.append(' & '.join(
                [f'{"!" if n else ""}{m}@{s}' for m, s, n in group]))

        return ' | '.join(string)

    def __repr__(self) -> str:
        """
        this string can be used with `eval()` if you wanted to.
        """
        return f"Sieve('{str(self)}')"

    def __or__(self, other) -> 'Sieve':
        """
        returns a complex sieve with union on the other.

        @param other: a string, tuple, or sieve.
        """

        if not type(other) in [str, tuple, Sieve]:
            raise ValueError('you can only & str, tuple, and Sieves.')

        if isinstance(other, str):
            other = Sieve(other)

        if isinstance(other, tuple):
            other = Sieve(*other)

        if isinstance(other, Sieve):
            if other.stype == 'simple':
                push = [(other._residuals[0][0])]
            elif other.stype == 'compound':
                push = [(residual[0], residual[1], residual[2])
                        for residual in other._residuals[0]]

            new = Sieve(self)
            new._residuals.append(push)

            return new

    def __and__(self, other) -> 'Sieve':
        """
        returns a sieve after applying an and operation to the last available
        residual. this means, if you chain multiple groups using | it will actually
        only add this operation to the last group.

        @param other: either a string, a tuple, or a simple or compound sieve
        @returns a sieve, either compound or complex.
        """

        if not type(other) in [str, tuple, Sieve]:
            raise ValueError('you can only & str, tuple, and Sieves.')

        if isinstance(other, str):
            other = Sieve(other)

        if isinstance(other, tuple):
            other = Sieve(*other)

        if isinstance(other, Sieve):
            if other.stype == 'simple':
                push = [(other._residuals[0][0])]
            elif other.stype == 'compound':
                push = [(residual[0], residual[1], residual[2])
                        for residual in other._residuals[0]]

            new = Sieve(self)
            new._residuals[-1 if self._cur_group ==
                           'last' else self._cur_group] += push

            return new


if __name__ == '__main__':
    # s = Sieve('4@2 & !1 | 3@2 & 7 & 9@2')
    s = Sieve(1, 7)
    s = s & '3@1' & (7, 3, False)
    # print(for_iter(s._residuals[0][0], range(128)))
    s = s.simplified | s
    # simps = simplify_group(s._residuals[0])
    # print(s.stype, 'sieve', simps)
    print(s)

    # input()
    # help(__name__)
    # print(s.stype)
    # print(s._residuals)
    # print(s._sieve_type, s._residuals)
    # print(parse_residual('!5@2'), parse_residual('  5'))  # should be (5, 2, True) (5, 0, False)
    # print(parse_sieve_str('4@2 & !1 | 3@2 & 7 & 9@2'))
