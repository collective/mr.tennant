# Copyright (C) 2007-2008 by Dr. Dieter Maurer, Illtalstr. 25, D-66571 Bubach, Germany
# see "LICENSE.txt" for details
#       $Id: __init__.py,v 1.2 2009/02/01 13:47:59 dieter Exp $
'''Tools to access historical ZODB state.

Will not work with ZODB 3.2, tested with ZODB 3.4 (may work with later
ZODB releases).
'''
from DateTime import DateTime

from connection import Connection

def getObjectAt(obj, time):
  '''return *obj* as it has been at *time*.

  *time* may be a 'DateTime' object or a time in seconds since epoch
  (or a serial/transactionid).

  *obj* and all (direct or indirect) persistent references are
  as of *time*.

  Raises 'POSKeyError' when the state cannot be found.
  '''
  c = Connection(obj._p_jar, time)
  c.open()
  return c[obj._p_oid]


def getHistory(obj, first=0, last=20):
  '''return history records for *obj* between *first* and *last* (indexes).

  The result is a sequence of dicts with "speaking" keys.
  '''
  try: parent = obj.aq_inner.aq_parent
  except AttributeError: parent = None
  oid = obj._p_oid; jar = obj._p_jar
  history = jar.db().history(oid, last, None)[first:]
  for d in history:
    d['time'] = DateTime(d['time'])
    try:
        hObj = getObjectAt(obj, d['tid'])
    except:
        continue
    if parent is not None and hasattr(hObj, '__of__'):
      hObj = hObj.__of__(parent)
    d['obj'] = hObj
  return history


def generateHistory(obj):
  """generator version of 'getHistory'."""
  first, last = 0, 2
  while True:
    history = getHistory(obj, first, last)
    if not history: raise StopIteration()
    for d in history: yield d
    first = last; last *= 2
  

def generateBTreeHistory(btree):
  """generate history records for *btree*.

  Try to combine with the changes to the persistent subobjects of *btree*.
  Note: the history may not be complete. Some deletion records may be
  missing (affected are deletion sequences that remove a complete persistent
  subobject). However, as least a single record refers to the missing
  deletions.
  """
  from BTrees.check import Walker
  from heapq import heapify, heappop, heapreplace

  class CollectSubobjects(Walker):
    """collect all persistent subobjects."""
    def __init__(self, obj):
      Walker.__init__(self, obj)
      self.subobjects = [obj]

    def visit_btree(self, obj, path, parent, is_mapping, keys, kids, lo, hi):
      if not path and len(kids) == 1: return # faked kid 
      self.subobjects.extend(kids)

    def visit_bucket(*args, **kw): pass

  class HeapAdapter(object):
    """history generator as heap element.

    'value' is a current history element (or 'None')
    """
    def __init__(self, obj):
      self.gen = generateHistory(obj)
      self.next()

    def next(self):
      value = None
      try: value = self.gen.next()
      except StopIteration: del self.gen
      self.value = value
      return value

    def __cmp__(self, other):
      """let larger transaction ids lead to smaller objects."""
      return - cmp(self.value['tid'], other.value['tid'])

  
  col = CollectSubobjects(btree); col.walk()
  heap = map(HeapAdapter, col.subobjects)
  heap = [a for a in heap if a.value is not None]
  heapify(heap)

  ctid = None
  while heap:
    a = heap[0]
    hr = a.value
    if ctid is None or hr['tid'] != ctid:
      ctid = hr['tid']
      hr['obj'] = getObjectAt(btree, ctid) 
      yield hr
    if a.next() is None: heappop(heap)
    else: heapreplace(heap, a)
  raise StopIteration()

