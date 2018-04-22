# -*- coding: utf-8 -*-

"""
Unit tests for `apsg` core module.

Use this steps for unit test:

- Arrange all necessary preconditions and inputs.
- Act on the object or method under test.
- Assert that the expected results have occurred.


Proper unit tests should fail for exactly one reason
(that’s why you should be using one assert per unit test.)
"""


import pytest
import numpy as np


from apsg import Vec, Fol, Lin, Fault, Pair, Group, DefGrad, Ortensor, settings


# ############################################################################
# Helpers
# ############################################################################


def is_hashable(obj):
    try:
        hash(obj)
        return True
    except:
        return False


# ############################################################################
# Vector
# ############################################################################


@pytest.mark.skip
def test_that_vector_is_hashable():
    assert is_hashable(Vec([1, 2, 3]))


def test_that_Vec_string_gets_three_digits_when_vec2dd_settings_is_false():
    settings["vec2dd"] = False

    vec = Vec([1, 2, 3])

    current = str(vec)
    expects = "V(1.000, 2.000, 3.000)"

    assert current == expects


def test_that_Vec_string_gets_dip_and_dir_when_vec2dd_settings_is_true():
    settings["vec2dd"] = True

    vec = Vec([1, 2, 3])

    current = str(vec)
    expects = "V:63/53"

    assert current == expects

    settings["vec2dd"] = False


# ``==`` operator


def test_that_equality_operator_is_reflexive():
    u = Vec(1, 2, 3)

    assert u == u


def test_that_equality_operator_is_symetric():
    u = Vec([1, 2, 3])
    v = Vec([1, 2, 3])

    assert u == v and v == u


def test_that_equality_operator_is_transitive():
    u = Vec([1, 2, 3])
    v = Vec([1, 2, 3])
    w = Vec([1, 2, 3])

    assert u == v and v == w and u == w


def test_that_equality_operator_precision_limits():
    """
    This is not the best method how to test a floating point precision limits,
    but I will keep it here for a future work.
    """
    lhs = Vec([1.00000000000000001] * 3)
    rhs = Vec([1.00000000000000009] * 3)

    assert lhs == rhs


def test_that_equality_operator_returns_false_for_none():
    lhs = Vec([1, 0, 0])
    rhs = None

    current = lhs == rhs
    expects = False

    assert current == expects


# ``!=`` operator


def test_inequality_operator():
    lhs = Vec([1, 2, 3])
    rhs = Vec([3, 2, 1])

    assert lhs != rhs


# ``hash``


@pytest.mark.skip
def test_that_hash_is_same_for_identical_vectors():
    lhs = Vec([1, 2, 3])
    rhs = Vec([1, 2, 3])

    assert hash(lhs) == hash(rhs)


@pytest.mark.skip
def test_that_hash_is_not_same_for_different_vectors():
    lhs = Vec([1, 2, 3])
    rhs = Vec([3, 2, 1])

    assert not hash(lhs) == hash(rhs)


# ``upper``


def test_that_vector_is_upper():
    vec = Vec([0, 0, -1])

    assert vec.upper


def test_that_vector_is_not_upper():
    vec = Vec([0, 0, 1])

    assert not vec.upper


# ``flip``


def test_that_vector_is_flipped():
    current = Vec([0, 0, 1]).flip
    expects = Vec([0, 0, -1])

    assert current == expects


# ``abs``


def test_absolute_value():
    current = abs(Vec([1, 2, 3]))
    expects = 3.7416573867739413

    assert current == expects


# ``uv``


def test_that_vector_is_normalized():
    current = Vec([1, 2, 3]).uv
    expects = Vec([0.26726124191242442, 0.5345224838248488, 0.8017837257372732])

    assert current == expects


# ``dd``


def test_dipdir():
    v = Vec([1, 0, 0])

    current = v.dd
    expects = (0.0, 0.0)

    assert current == expects


# fixme ``aslin``


def test_aslin_conversion():
    assert str(Vec([1, 1, 1]).aslin) == 'L:45/35'


def test_lin_to_vec_to_lin():
    assert Vec(Lin(110, 37)).aslin == Lin(110, 37)


# fixme ``asfol``


def test_asfol_conversion():
    assert str(Vec([1, 1, 1]).asfol) == 'S:225/55'


def test_fol_to_vec_to_fol():
    assert Vec(Fol(213, 52)).asfol == Fol(213, 52)


# todo ``asvec``


# ``angle``


def test_that_angle_between_vectors_is_0():
    lhs = Vec([1, 0, 0])
    rhs = Vec([1, 0, 0])

    current = lhs.angle(rhs)
    expects = 0 # degrees

    assert current == expects


def test_that_angle_between_vectors_is_90():
    lhs = Vec([1, 0, 0])
    rhs = Vec([0, 1, 1])

    current = lhs.angle(rhs)
    expects = 90 # degrees

    assert current == expects


def test_that_angle_between_vectors_is_180():
    lhs = Vec([1, 0, 0])
    rhs = Vec([-1, 0, 0])

    current = lhs.angle(rhs)
    expects = 180 # degrees

    assert current == expects


# ``cross``


def test_cross_product_of_colinear_vectors():

    lhs = Vec([1, 0, 0])
    rhs = Vec([-1, 0, 0])

    current = lhs.cross(rhs)
    expects = Vec([0, 0, 0])

    assert current == expects


def test_cross_product_of_orthonormal_vectors():
    e1 = Vec([1, 0, 0])
    e2 = Vec([0, 1, 0])

    current = e1.cross(e2)
    expects = Vec([0, 0, 1])

    assert current == expects


# ``dot``


def test_dot_product_of_same_vectors():
    i = Vec(1, 0, 0)
    j = Vec(1, 0, 0)

    assert i.dot(j) == abs(i) == abs(i)


def test_dot_product_of_orthonornal_vectors():
    i = Vec(1, 0, 0)
    j = Vec(0, 1, 0)

    assert i.dot(j) == 0


# ``rotate``


@pytest.fixture
def x():
    return Vec([1, 0, 0])


@pytest.fixture
def y():
    return Vec([0, 1, 0])


@pytest.fixture
def z():
    return Vec([0, 0, 1])


def test_rotation_by_90_around(z):
    v = Vec([1, 1, 1])
    current = v.rotate(z, 90)
    expects = Vec([-1, 1, 1])

    assert current == expects


def test_rotation_by_180_around(z):
    v = Vec([1, 1, 1])
    current = v.rotate(z, 180)
    expects = Vec([-1, -1, 1])

    assert current == expects


def test_rotation_by_360_around(z):
    v = Vec([1, 1, 1])
    current = v.rotate(z, 360)
    expects = Vec([1, 1, 1])

    assert current == expects


# ``project``


def test_projection_of_xy_onto(z):
    xz = Vec([1, 0, 1])
    current = xz.proj(z)
    expects = Vec([0, 0, 1])

    assert current == expects


# todo ``H``


# todo ``transform``


# ``+`` operator


def test_add_operator():
    lhs = Vec([1, 1, 1])
    rhs = Vec([1, 1, 1])

    current = lhs + rhs
    expects = Vec([2, 2, 2])

    assert current == expects


# ``-`` operator


def test_sub_operator():
    lhs = Vec([1, 1, 1])
    rhs = Vec([1, 1, 1])

    current = lhs - rhs
    expects = Vec([0, 0, 0])

    assert current == expects


# ``*`` operator aka dot product


def test_mull_operator():
    lhs = Vec([1, 1, 1])
    rhs = Vec([1, 1, 1])

    current = lhs * rhs
    expects = lhs.dot(rhs)

    assert current == expects


# ``**`` operator aka cross product


def test_pow_operator_with_vector():
    lhs = Vec([1, 0, 0])
    rhs = Vec([0, 1, 0])

    current = lhs ** rhs
    expects = lhs.cross(rhs)

    assert current == expects


def test_pow_operator_with_scalar():
    lhs = 2
    rhs = Vec([1, 1, 1])

    current = lhs * rhs
    expects = Vec([2, 2, 2])

    assert current == expects


# ``len``


def test_length_method():
    u = Vec([1])
    v = Vec([1, 2])
    w = Vec([1, 2, 3])

    len(u) == len(v) == len(w) == 3


# ``[]`` operator


def test_getitem():
    v = Vec([1, 2, 3])
    assert all((v[0] == 1, v[1] == 2, v[2] == 3))


# ############################################################################
# Group
# ############################################################################


def test_rotation_rdegree():
    g = Group.randn_lin()
    assert np.allclose(g.rotate(Lin(45, 45), 90).rdegree, g.rdegree)


def test_rotation_angle_lin():
    l1, l2 = Group.randn_lin(2)
    D = DefGrad.from_axis(Lin(45, 45), 60)
    assert np.allclose(l1.angle(l2), l1.transform(D).angle(l2.transform(D)))


def test_rotation_angle_fol():
    f1, f2 = Group.randn_fol(2)
    D = DefGrad.from_axis(Lin(45, 45), 60)
    assert np.allclose(f1.angle(f2), f1.transform(D).angle(f2.transform(D)))


def test_resultant_rdegree():
    g = Group.from_array([45, 135, 225, 315], [45, 45, 45, 45], Lin)
    c1 = g.R.uv == Lin(0, 90)
    c2 = np.allclose(abs(g.R), np.sqrt(8))
    c3 = np.allclose((g.rdegree/100 + 1)**2, 2)
    assert c1 and c2 and c3


def test_group_heterogenous_error():
    with pytest.raises(Exception) as exc:
        g = Group([1, 2, 3])
        assert "Data must be Fol, Lin or Vec type." ==  str(exc.exception)


# ############################################################################
# Lineation
# ############################################################################


def test_cross_product():
    l1 = Lin(110, 22)
    l2 = Lin(163, 47)
    p = l1**l2
    assert np.allclose(p.angle(l1), p.angle(l2), 90)


def test_axial_addition():
    l1, l2 = Group.randn_lin(2)
    assert l1.transform(l1.H(l2)) == l2


def test_vec_H():
    m = Lin(135, 10) + Lin(315, 10)
    assert m.uv == Lin(135, 0)


def test_group_heterogenous_error():
    with pytest.raises(Exception) as exc:
        g = Group([Fol(10, 10), Lin(20, 20)])
        assert "All data in group must be of same type." == str(exc.exception)


def test_pair_misfit():
    n, l = Group.randn_lin(2)
    f = n.asfol
    p = Pair.from_pair(f, f - l.proj(f))
    assert np.allclose(p.misfit, 0)


def test_pair_rotate():
    n, l = Group.randn_lin(2)
    f = n.asfol
    p = Pair.from_pair(f, f - l.proj(f))
    pr = p.rotate(Lin(45, 45), 120)
    assert np.allclose(p.fvec.angle(p.lvec), pr.fvec.angle(pr.lvec), 90)


def test_lin_vector_dd():
    l = Lin(120, 30)
    assert Lin(*l.V.dd) == l


# ############################################################################
# Foliation
# ############################################################################


def test_fol_vector_dd():
    f = Fol(120, 30)
    assert Lin(*f.V.dd).asfol == f


# ############################################################################
# Fault
# ############################################################################


def test_fault_rotation_sense():
    f = Fault(90, 30, 110, 28, -1)
    assert repr(f.rotate(Lin(220, 10), 60)) == 'F:343/37-301/29 +'


# ############################################################################
# Ortensor
# ############################################################################


def test_ortensor_orthogonal():
    f = Group.randn_fol(1)[0]
    assert np.allclose(*Ortensor(Group([f.V, f.rake(-45), f.rake(45)])).eigenvals)
