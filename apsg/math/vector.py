# -*- coding: utf-8 -*-


"""
A vector algebra types and functions.
"""


from apsg.math.scalar import Scalar
from apsg.math.matrix import Matrix


class NonConformableVectors(Exception): # Derive from matrix exception?
    """
    Raises when vectors are not conformable for a certain operation.
    """


class Vector(Matrix):
    """
    A column vector base class represented as N x 1 matrix.
    """

    def __init__(self, *elements):
        super(Vector, self).__init__(*elements)

    def __getitem__(self, index):
        return self._elements[index]


class Vector2(Vector):
    """
    Represents a two-dimensional column vector.

    Examples:
        >>> u = Vector2(1, 0)
        >>> v = Vector2(0, 1)
        >>> u + v
        Vector2([(1,), (1,)])

        # FIXME We want this ``Vector2(1, 1)``!
    """

    __shape__ = (2, 1)

    def __init__(self, *elements):
        expected_number_of_elements = self.__shape__[0] * self.__shape__[1]

        if len(elements) > expected_number_of_elements:
            raise WrongNumberOfElements(
                "Wrong number of elements, expected {0}, got {1}".format(
                    expected_number_of_elements, len(elements)))

        super(Vector2, self).__init__(*elements)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @classmethod
    def unit_x(cls):
        return cls(1, 0)

    @classmethod
    def unit_y(cls):
        return cls(0, 1)


class Vector3(Vector):
    """
    Represents a three-dimensional column vector.
    """

    __shape__ = (3, 1)

    def __init__(self, *elements):
        expected_number_of_elements = self.__shape__[0] * self.__shape__[1]

        if len(elements) > expected_number_of_elements:
            raise WrongNumberOfElements(
                "Wrong number of elements, expected {0}, got {1}".format(
                    expected_number_of_elements, len(elements)))

        super(Vector3, self).__init__(*elements)

    def __pow__(self, other):  # (Vector3) -> Vector3
        """
        Calculate the vector product between ``self`` and ``other`` vector.

        Returns:
            The vector product of ``self`` and ``other`` vector.
        """
        return self.__class__(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @classmethod
    def unit_x(cls):  # e1
        return cls(1, 0, 0)

    @classmethod
    def unit_y(cls):  # e2
        return cls(0, 1, 0)

    @classmethod
    def unit_z(cls):  # e3
        return cls(0, 0, 1)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    def cross(self, other):  # (Vector3) -> Vector3
        """
        Calculate the vector product between ``self`` and ``other`` vector.

        Returns:
            The vector product of ``self`` and ``other`` vector.
        """
        return self ** other


class Vector4(Vector):
    """
    Represents a four-dimensional column vector.
    """

    __shape__ = (4, 1)

    def __init__(self, *elements):
        expected_number_of_elements = self.__shape__[0] * self.__shape__[1]

        if len(elements) > expected_number_of_elements:
            raise WrongNumberOfElements(
                "Wrong number of elements, expected {0}, got {1}".format(
                    expected_number_of_elements, len(elements)))

        super(Vector3, self).__init__(*elements)

    @classmethod
    def unit_x(cls):
        return cls(1, 0, 0, 0)

    @classmethod
    def unit_y(cls):
        return cls(0, 1, 0, 0)

    @classmethod
    def unit_z(cls):
        return cls(0, 0, 1, 0)

    @classmethod
    def unit_w(cls):
        return cls(0, 0, 0, 1)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    @property
    def w(self):
        return self[3]
