"""Miscellaneous tools, somewhat random mix yet often helpful."""

from __future__ import division

import numpy as np

try:
    """you can ``pip install bottleneck`` to use this framework for fast NaN processing"""
    import bottleneck as bn
    has_bottleneck = True
except:
    has_bottleneck = False

all = ['to_iterable', 'to_ndarray', 'anynan', 'argsort', 'inverse_permutation',
       'list_to_dict_list', 'atleast_2d_pad', 'transpose_list_list', 'zero_if_close', 'pad']


def to_iterable(a):
    """If `a` is a not iterable or a string, return ``[a]``, else return ``a``."""
    if type(a) == str:
        return [a]
    try:
        iter(a)
    except TypeError:
        return [a]
    else:
        return a


def to_ndarray(a, array_size=None):
    """Convert to an 1D numpy array. If required, tile to the required size.

    Parameters
    ----------
    a :
        the input to be converted to an array. If a is not iterable, use `[a]`.
    array_size : int
        the desired lenght of the array. If not None, repeat `a` periodically to fit the len.

    Raises
    ------
    ValueError : if the len of a is not a divisor of `array_size`
    """
    try:
        iter(a)
    except TypeError:
        a = np.array([a])
    else:
        a = np.array(a)
    if array_size is not None:
        if array_size % len(a) != 0:
            raise ValueError("incomensurate len")
        a = np.tile(a, array_size // len(a))
    return a


if has_bottleneck:
    anynan = bn.anynan
else:
    def anynan(a):
        """check whether any entry of a ndarray `a` is 'NaN'"""
        return np.isnan(np.sum(a))  # still faster than 'np.isnan(a).any()'


def argsort(a, sort=None, **kwargs):
    """wrapper around np.argsort to allow sorting ascending/descending and by magnitude.

    Parameters
    ----------
    a : array_like
        the array to sort
    sort : {'m>', 'm<', '>', '<', ``None``}
        Specify how the arguments should be sorted.

        ===========  ===========================
        `sort`       order
        ===========  ===========================
        'm>', 'LM'   Largest magnitude first
        'm<', 'SM'   Smallest magnitude first
        '>', 'LR'    Largest real part first
        '<', 'SR'    Smallest real part first
        'LI'
        'SR'
        ``None``     numpy default: same as '<'
        ===========  ===========================
    **kwargs :
        further keyword arguments given directly to ``numpy.argsort``.

    Returns
    -------
    index_array : ndarray, int
        same shape as `a`, such that ``a[index_array]`` is sorted in the specified way.
    """
    if sort is not None:
        if sort == 'm<' or sort == 'SM':
            a = np.abs(a)
        elif sort == 'm>' or sort == 'LM':
            a = -np.abs(a)
        elif sort == '<' or sort == 'SR':
            a = np.real(a)
        elif sort == '>' or sort == 'LR':
            a = -np.real(a)
        elif sort == 'SI':
            a = np.imag(a)
        elif sort == 'LI':
            a = -np.imag(a)
        else:
            raise ValueError("unknown sort option " + repr(sort))
    return np.argsort(a, **kwargs)


def lexsort(a, axis=-1):
    """wrapper around ``np.lexsort``: allow for trivial case ``a.shape[0] = 0`` without sorting"""
    if any([s == 0 for s in a.shape]):
        return np.arange(a.shape[axis], dtype=np.intp)
    return np.lexsort(a, axis=axis)


def inverse_permutation(perm):
    """reverse sorting indices.

    Sort functions (as :meth:`LegCharge.sort`) return a (1D) permutation `perm` array,
    such that ``sorted_array = old_array[perm]``.
    This function inverts the permutation `perm`,
    such that ``old_array = sorted_array[inverse_permutation(perm)]``.

    Parameters
    ----------
    perm : 1D array_like
        the permutation to be reversed. *Assumes* that it is a permutation with unique indices.
        If it is, ``inverse_permutation(inverse_permutation(perm)) == perm``.

    Returns
    -------
    inv_perm : 1D array (int)
        the inverse permutation of `perm`
    """
    # with O(n log(n)) not the fastes possible implementation, but sufficient for all our needs
    return np.argsort(perm)


def list_to_dict_list(l):
    """Given a list `l` of objects, construct a lookup table.

    This function will handle duplicate entries in `l`.

    Parameters
    ----------
    l: list (iterabele of immutable)
        A list of objects that can be converted to tuples to be used as keys for a dictionary.

    Returns
    -------
    lookup : dict
        A dictionary with (key, value) pairs ``(key):[i1,i2,...]``
        where ``i1, i2, ...`` are the indices where `key` is found in `l`:
        i.e. ``key == tuple(l[i1]) == tuple(l[i2]) == ...``
    """
    d = {}
    for i, r in enumerate(l):
        k = tuple(r)
        try:
            d[k].append(i)
        except KeyError:
            d[k] = [i]
    return d


def atleast_2d_pad(a, pad_item=0):
    """Transform `a` into a 2D array, filling missing places with `pad_item`.

    Given a list of lists, turn it to a 2D array (pad with 0), or turn a 1D list to 2D.

    Parameters
    ----------
    a : list of lists
        to be converted into ad 2D array.

    Returns
    -------
    a_2D : 2D ndarray
        a converted into a numpy array.

    Examples
    --------
    >>> atleast_2d_pad([3, 4, 0])
    array([[3, 4, 0]])

    >>> atleast_2d_pad([[3, 4],[1, 6, 7]])
    array([[ 3.,  4.,  0.],
           [ 1.,  6.,  7.]])

    """
    iter(a)  # check that a is at least 1D iterable
    if len(a) == 0:
        return np.zeros([0, 0])
    # Check if every element of a is a list
    is_list_of_list = True
    for s in a:
        try:
            iter(s)
        except TypeError:
            is_list_of_list = False
            break
    if not is_list_of_list:
        return np.array([a])
    maxlen = max([len(s) for s in a])
    # Pad if necessary
    a = [np.hstack([s, [pad_item]*(maxlen - len(s))]) for s in a]
    return np.array(a)


def transpose_list_list(D, pad=None):
    """Returns a list of lists T, such that ``T[i][j] = D[j][i]``.

    Parameters
    ----------
    D : list of list
        to be transposed
    pad :
        Used to fill missing places, if D is not rectangular.

    Returns
    -------
    T : list of lists
        transposed, rectangular version of `D`.
        constructed such that ``T[i][j] = D[j][i] if i < len(D[j]) else pad``
    """
    nRow = len(D)
    if nRow == 0:
        return [[]]
    nCol = max([len(R) for R in D])
    T = [[pad] * nRow for i in range(nCol)]
    for j, R in enumerate(D):
        for i, e in enumerate(R):
            T[i][j] = e
    return T


def zero_if_close(a, tol=1.e-15):
    """set real and/or imaginary part to 0 if their absolute value is smaller than `tol`.

    Parameters
    ----------
    a : ndarray
        numpy array to be rounded
    tol : float
        the threashold which values to consider as '0'.
    """
    if a.dtype == np.complex128 or a.dtype == np.complex64:
        ar = np.choose(np.abs(a.real) < tol, [a.real, np.zeros(a.shape)])
        ai = np.choose(np.abs(a.imag) < tol, [a.imag, np.zeros(a.shape)])
        return ar + 1j * ai
    else:
        return np.choose(np.abs(a) < tol, [a, np.zeros_like(a)])


def pad(a, w_l=0, v_l=0, w_r=0, v_r=0, axis=0):
    """Pad an array along a given `axis`.

    Parameters
    ----------
    a : ndarray
        the array to be padded
    w_l : int
        the width to be padded in the front
    v_l : dtype
        the value to be inserted before `a`
    w_r : int
        the width to be padded after the last index
    v_l : dtype
        the value to be inserted after `a`
    axis : int
        the axis along which to pad

    Returns
    -------
    padded : ndarray
        a copy of `a` with enlarged `axis`, padded with the given values.
    """
    shp = list(a.shape)
    shp[axis] += w_r + w_l
    b = np.empty(shp, a.dtype)
    # tuple of full slices
    take = [slice(None) for j in range(len(shp))]
    # prepend
    take[axis] = slice(w_l)
    b[tuple(take)] = v_l
    # copy a
    take[axis] = slice(w_l, -w_r)
    b[tuple(take)] = a
    # append
    take[axis] = slice(-w_r, None)
    b[tuple(take)] = v_r
    return b
