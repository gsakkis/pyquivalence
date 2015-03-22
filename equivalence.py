'''A pure Python implementation of equivalence relations.'''

__all__ = ['equivalence', 'Equivalence']
__docformat__ = "restructuredtext en"

from itertools import izip
from collections import defaultdict


def equivalence(key=None, bidirectional=False):
    '''Factory function for creating an appropriate `Equivalence` instance.

    To facilitate future API changes, all arguments to this function should be
    passed as keywords.

    :type key: None or callable ``key(x)``
    :param key: The key function to be used for determining implicit equivalence,
        or None if there is not a key function.
    :type bidirectional: bool
    :param bidirectional: If true, the `Equivalence.partition` method takes
        linear time to the size of the given object's equivalence set, as opposed
        to the size of the whole equivalence relation if `bidirectional` is false.
        The downside is increased memory overhead and extra constant factor cost
        for the rest methods.
    :rtype: `Equivalence`
    '''
    if key is None:
        return (bidirectional and BidirectionalEquivalence or Equivalence)()
    else:
        return (bidirectional and KeyBidirectionalEquivalence or KeyEquivalence)(key)


class Equivalence(object):
    '''Basic equivalence relation.

    An `Equivalence` instance maintains a partition of objects into sets so that
    the equivalence properties (reflexivity, symmetry, transitivity) are preserved.
    Two objects ``a`` and ``b`` are considered equivalent after `merge(a,b)`.

    This implementation uses a `disjoint-set forests`_ data structure with
    *union by rank* and *path compression* so most operations have almost
    constant amortized time. The main exception is `partition`, which is linear
    to the size of the **whole equivalence** and should therefore be avoided for
    large relations.

    .. _`disjoint-set forests`: http://en.wikipedia.org/wiki/Disjoint-set_data_structure
    '''

    def __init__(self):
        '''Intialize this equivalence.'''
        # maps an object to its parent in the disjoint-set forest
        self._child2parent = {}
        # maps an object to its rank in the disjoint-set
        self._rank = {}

    def update(self, *objects):
        '''Update this equivalence with the given objects.'''
        join,rank,child2parent = self._join,self._rank,self._child2parent
        for obj in objects:
            if obj not in child2parent:
                join(obj)
                rank[obj] = 0

    def merge(self, *objects):
        '''Merge all the given objects into the same equivalence set.'''
        if not objects: return
        join,rank,find = self._join,self._rank,self._find
        objects = iter(objects)
        root = find(objects.next(), True)
        for obj in objects:
            root2 = find(obj,True)
            # union-by-rank
            cmp_rank = cmp(rank[root], rank[root2])
            if cmp_rank > 0:
                join(root2,root)
            elif cmp_rank < 0:
                join(root,root2)
            elif cmp_rank == 0 and root != root2:
                rank[root] += 1
                join(root2,root)

    def are_equivalent(self, *objects):
        '''Check whether all objects are equivalent.

        An object doesn't have to be in the equivalence (through `update` or
        `merge`) in order to appear as an argument.

        :rtype: bool
        '''
        if not objects:
            raise ValueError('No objects given')
        find = self._find
        objects = iter(objects)
        root = find(objects.next())
        for obj in objects:
            if find(obj) != root:
                return False
        return True

    def partitions(self, objects=None):
        '''Return the partitioning of `objects` into equivalence groups.

        :type objects: Iterable or None
        :param objects: If not None, it must be an iterable of objects to be
            partitioned. Otherwise, it defaults to the objects already inserted
            in the equivalence (through `update` and `merge`).
        :rtype: list of lists
        :returns: A list of partitions, each partition being a list of equivalent
            objects. Note that if the passed argument contains duplicates, so
            will the respective partition list, i.e. the partition is not a set.
        '''
        find = self._find
        key2partition = defaultdict(list)
        if objects is None:
            objects = self._iter_objects()
        for obj in objects:
            key2partition[find(obj)].append(obj)
        return key2partition.values()

    def partition(self, obj):
        '''Return the set of objects in the equivalence that are equivalent to
        `obj`.

        :attention: This implementation is linear to the number of objects in the
            equivalence. If you call this a lot, you might want to use a
            `BidirectionalEquivalence` instance instead.

        :rtype: set
        '''
        find = self._find
        root = find(obj)
        return set(obj for obj in self._child2parent if find(obj) == root)

    #--------- 'protected' methods ---------------------------------------------

    def _find(self, obj, insert_if_missing=False):
        '''The 'find' part of the union-find algorithm.

        :param obj: The object whose tree root is to be returned.
        :type insert_if_missing: bool
        :param insert_if_missing: If true and `obj` is not already in this
            equivalence, add it as a new singleton tree.
        :returns: The root of `obj`'s tree.
        '''
        if obj not in self._child2parent:
            if insert_if_missing:
                self._join(obj)
                self._rank[obj] = 0
        else:
            parent = self._child2parent[obj]
            if parent is not None:
                root = self._find(parent)
                self._join(obj, root)   # path compression
                obj = root
        return obj

    def _join(self, obj, parent=None):
        '''Join `obj` to its parent (or None if it's the root).'''
        self._child2parent[obj] = parent

    def _iter_objects(self):
        '''Return an iterator over all the objects of the equivalence.'''
        return self._child2parent.iterkeys()


class BidirectionalEquivalence(Equivalence):
    '''Equivalence with fast `partition` method.

    This class implements a `partition` method that takes linear time to the size
    of the respective partition, as opposed to the size of the whole equivalence.
    The downside is increased memory overhead and extra constant factor cost for
    the rest methods.
    '''

    def __init__(self):
        super(BidirectionalEquivalence,self).__init__()
        # inverted mapping of self._child2parent
        self._parent2children = defaultdict(set)

    def partition(self, obj):
        '''Return the set of objects in the equivalence that are equivalent to
        `obj`.

        :rtype: set
        '''
        p = set()
        if obj in self._child2parent:
            def recurse(node, get_children=self._parent2children.get, add=p.add):
                add(node)
                for child in get_children(node, ()):
                    recurse(child)
            recurse(self._find(obj))
        return p

    def _join(self, obj, parent=None):
        super(BidirectionalEquivalence,self)._join(obj, parent)
        if parent is not None:
            self._parent2children[parent].add(obj)


class KeyEquivalence(Equivalence):
    '''Class that maintains object equivalence with respect to a key function.

    Given a function ``key(x)``, two objects ``a`` and ``b`` are considered
    equivalent if ``key(a) == key(b)``. Of course, since this class is an
    `Equivalence`, ``a`` and ``b`` are also equivalent after `merge(a,b)`, even
    if their keys are different.
    '''

    def __init__(self, key):
        '''Initialize this equivalence.

        :param key: A callable to be used for determining key equivalence. To
            ensure that the equivalence properties are preserved, ``key(x)``
            should remain fixed for a given object ``x``, i.e. it should be
            deterministic and not depend on any mutable state of ``x``.
        '''
        super(KeyEquivalence,self).__init__()
        self._keyfunc = key
        # map each key to the set of objects in the equivalence with this key
        self._key2objects = defaultdict(set)

    def update(self, *objects):
        keys = self._update_key2objects(objects)
        super(KeyEquivalence,self).update(*keys)

    def merge(self, *objects):
        self._update_key2objects(objects)
        super(KeyEquivalence, self).merge(*objects)

    def partition(self, obj):
        p = set(); update = p.update
        get_objects = self._key2objects.get
        for key in super(KeyEquivalence,self).partition(self._keyfunc(obj)):
            update(get_objects(key,()))
        return p

    #--------- 'protected' methods ---------------------------------------------

    def _find(self, obj, insert_if_missing=False):
        return super(KeyEquivalence,self)._find(self._keyfunc(obj), insert_if_missing)

    def _iter_objects(self):
        return (o for objects in self._key2objects.itervalues() for o in objects)

    def _update_key2objects(self, objects):
        '''Update the _key2objects data structure.

        :returns: The keys of the passed objects.
        '''
        key2objects = self._key2objects
        keys = map(self._keyfunc, objects)
        for key,obj in izip(keys, objects):
            key2objects[key].add(obj)
        return keys


class KeyBidirectionalEquivalence(KeyEquivalence,BidirectionalEquivalence):
    '''A `KeyEquivalence` that is also `BidirectionalEquivalence`.'''
