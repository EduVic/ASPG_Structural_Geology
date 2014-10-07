# -*- coding: utf-8 -*-
"""
Python module to manipulate, analyze and visualize structural geology data

Example::

    from apsg import *
    d=Dataset(name='lineace')
    d.append(Lin(120,40))
    d.append(Lin(153,18))
    d.append(Lin(140,35))
    s=SchmidtNet(d)
    s.add(d[0]**d[1])
    s.show()

"""

# import modulu
from __future__ import division, print_function
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# lambda funkce
sind = lambda x: np.sin(np.deg2rad(x))
cosd = lambda x: np.cos(np.deg2rad(x))
asind = lambda x: np.rad2deg(np.arcsin(x))
acosd = lambda x: np.rad2deg(np.arccos(x))
atan2d = lambda x1, x2: np.rad2deg(np.arctan2(x1, x2))
getldd = lambda x, y: (atan2d(x, y) % 360, 90-2*asind(np.sqrt((x*x + y*y)/2)))
getfdd = lambda x, y: (atan2d(-x, -y) % 360, 2*asind(np.sqrt((x*x + y*y)/2)))
getldc = lambda u, v: (cosd(u)*cosd(v), sind(u)*cosd(v), sind(v))
getfdc = lambda u, v: (-cosd(u)*sind(v), -sind(u)*sind(v), cosd(v))

class Vec3(np.ndarray):
    """Base class to store 3D vectors derived from numpy.ndarray
    """
    def __new__(cls, array):
        # casting na nasi tridu
        obj = np.asarray(array).view(cls)
        return obj

    def __repr__(self):
        return 'V' + '(%.3f, %.3f, %.3f)' % tuple(self)

    def __mul__(self, other):
        # nasobeni je skalarni soucin
        return np.dot(self, other)

    def __abs__(self):
        # abs vrati delku vektoru
        return np.sqrt(self * self)

    def __pow__(self, other):
        # vektorovy soucin nebo mocnina delky vektoru
        if np.isscalar(other):
            return pow(abs(self), other)
        else:
            return Vec3(np.cross(self, other))

    def __eq__(self, other):
        # jsou stejne
        return abs(self - other) < 1e-15

    def __ne__(self, other):
        # nejsou stejne
        return not self == other

    def getuv(self):
        """Return unit vector

        >>> u = Vec3([1,1,1])
        >>> u.getuv()
        V(0.577, 0.577, 0.577)
        """
        return self/abs(self)

    def aslin(self):
        """Convert vector to Lin object.

        >>> u = Vec3([1,1,1])
        >>> u.aslin()
        L:45/35
        """
        res = Lin(0, 0)
        np.copyto(res, self)
        return res

    def asfol(self):
        """Convert vector to Fol object.

        >>> u = Vec3([1,1,1])
        >>> u.asfol()
        S:225/55
        """
        res = Fol(0, 0)
        np.copyto(res, self)
        return res

    def aspole(self):
        """Convert vector to Pole object.

        >>> u = Vec3([1,1,1])
        >>> u.aspole()
        P:225/55
        """
        res = Pole(0, 0)
        np.copyto(res, self)
        return res

    def cross(self, other):
        """Returns cross product of two vectors

        :param vec: vector
        :type name: Vec3
        :returns:  Vec3

        >>> v=Vec3([0,2,-2])
        >>> u.cross(v)
        V(-4.000, 2.000, 2.000)
        """
        return Vec3(np.cross(self, other))

    def angle(self, other):
        """Returns angle of two vectors in degrees

        :param vec: vector
        :type name: Vec3
        :returns:  Vec3

        >>> u.angle(v)
        90.0
        """
        return acosd(np.dot(self.getuv(), other.getuv()))

    def rotate(self, axis, phi):
        """Rotate vector phi degrees about axis

        :param axis: vector
        :type name: Vec3
        :param phi: angle of rotation
        :returns:  Vec3

        >>> v.rotate(u,60)
        V(-2.000, 2.000, -0.000)
        """
        k = axis.getuv()
        return cosd(phi)*self + sind(phi)*k.cross(self) + \
               (1-cosd(phi))*k*(k*self)

    def proj(self, other):
        '''
        Vrátí projekci vektoru *u* na vektor *v*::

            u.proj(v)
        '''
        return np.dot(self, other) * other / abs(other) ** 2


class Lin(Vec3):
    """Class for linear features
    """
    def __new__(cls, azi, inc):
        # casting na nasi tridu
        return Vec3(getldc(azi, inc)).view(cls)

    def __repr__(self):
        azi, inc = self.dd
        return 'L:%d/%d' % (round(azi), round(inc))

    def __add__(self, other):
        # soucet osnich dat
        if self * other < 0:
            other = -other
        return super(Lin, self).__add__(other)

    def __iadd__(self, other):
        # soucet osnich dat
        if self * other < 0:
            other = -other
        return super(Lin, self).__iadd__(other)

    def __sub__(self, other):
        # rozdil osnich dat
        if self * other < 0:
            other = -other
        return super(Lin, self).__sub__(other)

    def __isub__(self, other):
        # rozdil osnich dat
        if self * other < 0:
            other = -other
        return super(Lin, self).__isub__(other)

    def __pow__(self, other):
        # vektorovy soucin nebo mocnina delky vektoru
        if np.isscalar(other):
            return pow(abs(self), other)
        else:
            return super(Lin, self).cross(other).asfol()

    def __eq__(self, other):
        # jsou stejne
        return abs(self-other) < 1e-15 or abs(self+other) < 1e-15

    def __ne__(self, other):
        # nejsou stejne
        return not (self == other or self == -other)

    def angle(self, lin):
        """Returns angle of two lineations in degrees

        :param lin: lineation
        :type name: Lin
        :returns:  angle

        >>> u.angle(v)
        90.0
        """
        return acosd(abs(np.dot(self.getuv(), lin.getuv())))

    def cross(self, other):
        """Vrátí planární strukturní prvek definovaný dvěma lineárními
        prvky *k* a *l*::

            k.cross(l)

        Stejný výsledek je možné získat vektorovým součinem
        lineárních prvků::

            k**l
        """
        return Vec3(np.cross(self, other)).asfol

    def rotate(self, axis, phi):
        """Vrátí výsledek rotace lineárního prvku *l* o úhel *phi*
        kolem osy *a*::

            l.rotate(a, phi)

        Osa *a* je objekt třídy :class:`apsg.lin` anebo :class:`apsg.vec3`
        a úhel *phi* je ve stupních.
        """
        return Vec3(self).rotate(Vec3(axis), phi).aslin()

    def proj(self, other):
        """Vrátí projekci lineárního prvku *k* na prvek *l*::

            k.proj(l)
        """
        return np.dot(self, other) * Vec3(other).aslin()

    @property
    def dd(self):
        n = self.getuv()
        if n[2] < 0:
            n = -n
        azi = atan2d(n[1], n[0]) % 360
        inc = asind(n[2])
        return azi, inc

    def getxy(self):
        azi, inc = self.dd
        return (np.sqrt(2)*sind((90-inc)/2)*sind(azi), 
                np.sqrt(2)*sind((90-inc)/2)*cosd(azi))

class Fol(Vec3):
    """Class for planar features
    """
    def __new__(cls, azi, inc):
        # casting na nasi tridu
        return Vec3(getfdc(azi, inc)).view(cls)

    def __repr__(self):
        azi, inc = self.dd
        return 'S:%d/%d' % (round(azi), round(inc))

    def __add__(self, other):
        # soucet osnich dat
        if self * other < 0:
            other = -other
        return super(Fol, self).__add__(other)

    def __iadd__(self, other):
        # soucet osnich dat
        if self * other < 0:
            other = -other
        return super(Fol, self).__iadd__(other)

    def __sub__(self, other):
        # rozdil osnich dat
        if self * other < 0:
            other = -other
        return super(Fol, self).__sub__(other)

    def __isub__(self, other):
        # rozdil osnich dat
        if self * other < 0:
            other = -other
        return super(Fol, self).__isub__(other)

    def __pow__(self, other):
        # vektorovy soucin nebo mocnina delky vektoru
        if np.isscalar(other):
            return pow(abs(self), other)
        else:
            return super(Fol, self).cross(other).aslin()

    def __eq__(self, other):
        # jsou stejne
        return abs(self-other) < 1e-15 or abs(self+other) < 1e-15

    def __ne__(self, other):
        # nejsou stejne
        return not (self == other or self == -other)

    def angle(self, fol):
        """Returns angle of two foliations in degrees

        :param lin: foliation
        :type name: Fol
        :returns:  angle

        >>> u.angle(v)
        90.0
        """
        return acosd(abs(np.dot(self.getuv(), fol.getuv())))

    def cross(self, other):
        """Vrátí lineární strukturní prvek definovaný intersekcí
        dvou planárních prvků *f* a *g*::

            f.cross(g)

        Stejný výsledek je možné získat vektorovým součinem
        planárních prvků::

            f**g
        """
        return Vec3(np.cross(self, other)).aslin()

    def rotate(self, axis, phi):
        """Vrátí výsledek rotace planárního prvku *f* o úhel *phi*
        kolem osy *a*::

            f.rotate(a, phi)

        Osa *a* je objekt třídy :class:`apsg.lin` anebo :class:`apsg.vec3`
        a úhel *phi* je ve stupních.
        """
        return Vec3(self).rotate(Vec3(axis), phi).asfol()

    def proj(self, other):
        """Vrátí projekci planárního prvku *f* na prvek *g*::

            f.proj(g)
        """
        return np.dot(self, other) * Vec3(other).asfol()

    @property
    def dd(self):
        n = self.getuv()
        if n[2] < 0:
            n = -n
        azi = (atan2d(n[1], n[0]) + 180) % 360
        inc = 90 - asind(n[2])
        return azi, inc

    def getxy(self):
        azi, inc = self.dd
        return (-np.sqrt(2)*sind(inc/2)*sind(azi),
                -np.sqrt(2)*sind(inc/2)*cosd(azi))

class Pole(Fol):
    """Class for planar features represented as poles
    """
    def __new__(cls, azi, inc):
        # casting na nasi tridu
        return Vec3(getfdc(azi, inc)).view(cls)

    def __repr__(self):
        azi, inc = self.dd
        return 'P:%d/%d' % (round(azi), round(inc))

class Ortensor(object):
    """trida Ortensor"""
    def __init__(self, d):
        self.M = np.dot(np.array(d).T, np.array(d))
        self.n = len(d)
        vc, vv = np.linalg.eig(self.M)
        ix = np.argsort(vc)[::-1]
        self.vals = vc[ix]
        self.vects = vv.T[ix]
        e1, e2, e3 = self.vals / self.n
        self.shape = np.log(e3 / e2) / np.log(e2 / e1)
        self.strength = np.log(e3 / e1)

    def __repr__(self):
        return '(E1:%.4g,E2:%.4g,E3:%.4g)' % tuple(self.vals) + \
            '\n' + repr(self.M)

    def eigenvals(self, norm=True):
        if norm:
            n = self.n
        else:
            n = 1.0
        return self.vals[0] / n, self.vals[1] / n, self.vals[2] / n

    def eigenvects(self, scaled=False, norm=True):
        if scaled:
            e1, e2, e3 = self.eigenvals(norm=norm)
        else:
            e1 = e2 = e3 = 1.0
        return e1 * Vec3(self.vects[0]),\
               e2 * Vec3(self.vects[1]),\
               e3 * Vec3(self.vects[2])

    @property
    def eigenlins(self):
        v1, v2, v3 = self.eigenvects()
        d1 = Dataset(v1.aslin(), name='E1', color='red')
        d2 = Dataset(v2.aslin(), name='E2', color='magenta')
        d3 = Dataset(v3.aslin(), name='E3', color='green')
        return d1, d2, d3

    @property
    def eigenfols(self):
        v1, v2, v3 = self.eigenvects()
        d1 = Dataset(v1.asfol(), name='E1', color='red')
        d2 = Dataset(v2.asfol(), name='E2', color='magenta')
        d3 = Dataset(v3.asfol(), name='E3', color='green')
        return d1, d2, d3

class Dataset(list):
    """Class for dataset i.e. set of planar or linear features
    """
    def __init__(self, data=[],
                 name='Default',
                 color='blue',
                 lines={'lw':1, 'ls':'-'},
                 points={'marker':'o', 's':20},
                 poles={'marker':'v', 's':36,
                 'facecolors':None}):
        if not issubclass(type(data), list):
            data = [data]
        list.__init__(self, data)
        self.name = name
        self.color = color
        self.lines = lines
        self.points = points
        self.poles = poles
    def __repr__(self):
        return self.name + ':' + repr(list(self))

    def __add__(self, d2):
        # slouci datasety
        return Dataset(list(self) + d2, self.name, self.color,
                       self.lines, self.points, self.poles)

    def getlins(self):
        """Vrati pouze lineace z datasetu"""
        return Dataset([d for d in self if type(d) == Lin], self.name,
                        self.color, self.lines, self.points, self.poles)

    def getfols(self):
        """Vrati pouze foliace z datasetu"""
        return Dataset([d for d in self if type(d) == Fol], self.name,
                        self.color, self.lines, self.points, self.poles)

    def getpoles(self):
            """Vrati pouze poly z datasetu"""
            return Dataset([d for d in self if type(d) == Pole], self.name,
                            self.color, self.lines, self.points, self.poles)

    @property
    def numlins(self):
        """Vrati pocet lineaci v datasetu"""
        return len(self.getlins())

    @property
    def numfols(self):
        """Vrati pocet foliacii v datasetu"""
        return len(self.getfols())

    @property
    def numpoles(self):
        """Vrati pocet polu v datasetu"""
        return len(self.getpoles())

    def aslin(self):
        """Prevede vsechny data v datasetu na lineace"""
        return Dataset([d.aslin() for d in self], self.name, self.color,
                        self.lines, self.points, self.poles)

    def asfol(self):
        """Prevede vsechny data v datasetu na foliace"""
        return Dataset([d.asfol() for d in self], self.name, self.color,
                        self.lines, self.points, self.poles)

    def aspole(self):
        """Prevede vsechny data v datasetu na poly"""
        return Dataset([d.aspole() for d in self], self.name, self.color,
                        self.lines, self.points, self.poles)

    @property
    def resultant(self):
        """Vrati resultant vektor"""
        r = self[0]
        for v in self[1:]:
            r += v
        return r

    @property
    def rdegree(self):
        """Vrati stupen prednostni orientace"""
        r = self.resultant
        n = len(self)
        return 100*(2*abs(r) - n)/n

    def cross(self, d=None):
        """All pairs cross product"""
        res = Dataset(name='Pairs')
        if d == None:
            for i in range(len(self)-1):
                for j in range(i+1, len(self)):
                    res.append(self[i]**self[j])
        else:
            for i in range(len(self)):
                for j in range(len(d)):
                    res.append(self[i]**d[j])
        return res

    def rotate(self, axis, phi):
        """Rotace datasetu kolem osi axis o uhel phi"""
        dr = Dataset(name='R-' + self.name, color=self.color)
        for e in self:
            dr.append(e.rotate(axis, phi))
        return dr

    def center(self):
        """Centrovani smeru E3 do vertikalni polohy"""
        ot = self.ortensor
        azi, inc = ot.eigenlins[2][0].dd
        return self.rotate(Lin(azi - 90, 0), 90 - inc)

    def angle(self, other):
        """Vrati uhel mezi elementy datasetu a danym prvkem"""
        r = []
        for e in self:
            r.append(e.angle(other))
        return np.array(r)

    @property
    def ortensor(self):
        """Vrati orienacni tenzor"""
        return Ortensor(self)

    @property
    def dd(self):
        """Vratí pole azimutů a sklonů měření v datasetu"""
        return np.array([d.dd for d in self]).T

    def density(self, k=100, npoints=180):
        """Vrati density objekt"""
        return Density(self, k, npoints)

    def plot(self):
        """Show dataset on Schmidt net"""
        return SchmidtNet(self)

class Datasource(object):
    """PySDB database access class"""
    TESTSEL = "SELECT sites.id, sites.name, sites.x_coord, sites.y_coord, \
    sites.description, structdata.id, structdata.id_sites, \
    structdata.id_structype, structdata.azimuth, structdata.inclination, \
    structype.id, structype.structure, structype.description, \
    structype.structcode, structype.groupcode  \
    FROM sites \
    INNER JOIN structdata ON sites.id = structdata.id_sites \
    INNER JOIN structype ON structype.id = structdatnumlinsa.id_structype \
    LIMIT 1"
    STRUCTSEL = "SELECT structype.structure  \
    FROM sites  \
    INNER JOIN structdata ON sites.id = structdata.id_sites  \
    INNER JOIN structype ON structype.id = structdata.id_structype  \
    INNER JOIN units ON units.id = sites.id_units  \
    GROUP BY structype.structure  \
    ORDER BY structype.structure ASC"
    SELECT = "SELECT structdata.azimuth, structdata.inclination   \
    FROM sites   \
    INNER JOIN structdata ON sites.id = structdata.id_sites   \
    INNER JOIN structype ON structype.id = structdata.id_structype   \
    INNER JOIN units ON units.id = sites.id_units"
    def __new__(cls, db=None):
        try:
            cls.con = sqlite3.connect(db)
            cls.con.execute("pragma encoding='UTF-8'")
            cls.con.execute(Datasource.TESTSEL)
            print("Connected. PySDB version: %s" % cls.con.execute("SELECT value FROM meta WHERE name='version'").fetchall()[0][0])
            return super(Datasource, cls).__new__(cls)
        except sqlite3.Error as e:
            print("Error %s:" % e.args[0])
            raise sqlite3.Error

    @property
    def structures(self):
        return [element[0] for element in self.con.execute(Datasource.STRUCTSEL).fetchall()]

    def select(self, struct=None):
        fsel = Datasource.SELECT + " WHERE structype.planar=1"
        lsel = Datasource.SELECT + " WHERE structype.planar=0"
        if struct:
            fsel += " AND structype.structure='%s'" % struct
            lsel += " AND structype.structure='%s'" % struct
        fsel += " ORDER BY sites.name ASC"
        lsel += " ORDER BY sites.name ASC"

        fol = Dataset([Fol(element[0], element[1]) for element in self.con.execute(fsel).fetchall()])
        lin = Dataset([Lin(element[0], element[1]) for element in self.con.execute(lsel).fetchall()])
        return fol + lin

class Density(object):
    """trida Density"""
    def __init__(self, d, k=100, npoints=180):
        self.dcdata = np.asarray(d)
        self.calculate(k, npoints)

    def calculate(self, k, npoints=180):
        import matplotlib.tri as tri
        self.xg = 0
        self.yg = 0
        for rho in np.linspace(0, 1, np.round(npoints/2/np.pi)):
            theta = np.linspace(0, 360, np.round(npoints*rho + 1))[:-1]
            self.xg = np.hstack((self.xg, rho*sind(theta)))
            self.yg = np.hstack((self.yg, rho*cosd(theta)))
        self.dcgrid = np.asarray(getldc(*getldd(self.xg, self.yg)))
        n = len(self.dcdata)
        E = n/k  # some points on periphery are equivalent
        s = np.sqrt((n*(0.5-1/k)/k))
        w = np.zeros(len(self.xg))
        for i in range(n):
            w += np.exp(k*(np.abs(np.dot(self.dcdata[i], self.dcgrid))-1))
        self.density = (w-E)/s
        self.triang = tri.Triangulation(self.xg, self.yg)

    def plot(self, N=6, cm=plt.cm.jet):
        plt.figure()
        plt.gca().set_aspect('equal')
        plt.tricontourf(self.triang, self.density, N, cm=cm)
        plt.colorbar()
        plt.tricontour(self.triang, self.density, N, colors='k')
        plt.show()

    def plotcountgrid(self):
        plt.figure()
        plt.gca().set_aspect('equal')
        plt.triplot(self.triang, 'bo-')
        plt.show()

class SchmidtNet(object):
    """trida SchmidtNet"""
    def __init__(self, *data):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.grid = True
        self.data = []
        self.density = None
        self.nc = 6
        self.cm = plt.cm.Greys
        for arg in data:
            self.add(arg)
        if data:
            self.show()

    def clear(self):
        """odebere vsechny data"""
        self.data = []
        self.density = None
        self.nc = 6
        self.cm = plt.cm.Greys
        self.show()

    def getlin(self):
        """vrati Lin pomoci kliknuti mysi"""
        x, y = plt.ginput(1)[0]
        return Lin(*getldd(x, y))

    def getfol(self):
        """vrati Fol pomoci kliknuti mysi"""
        x, y = plt.ginput(1)[0]
        return Fol(*getfdd(x, y))

    def getpole(self):
        """vrati Pole pomoci kliknuti mysi"""
        x, y = plt.ginput(1)[0]
        return Pole(*getfdd(x, y))

    def getlins(self):
        """vrati Lin Dataset pomoci kliknuti mysi"""
        pts = plt.ginput(0, mouse_add=1, mouse_pop=2, mouse_stop=3)
        l = Dataset()
        for x, y in pts:
            l.append(Lin(*getldd(x, y)))
        return l

    def getfols(self):
        """vrati Fol Dataset pomoci kliknuti mysi"""
        pts = plt.ginput(0, mouse_add=1, mouse_pop=2, mouse_stop=3)
        f = Dataset()
        for x, y in pts:
            f.append(Fol(*getfdd(x, y)))
        return f

    def getpoles(self):
        """vrati Pole Dataset pomoci kliknuti mysi"""
        pts = plt.ginput(0, mouse_add=1, mouse_pop=2, mouse_stop=3)
        f = Dataset()
        for x, y in pts:
            f.append(Pole(*getfdd(x, y)))
        return f

    def add(self, *args):
        """Prida dataset do seznamu prvku"""
        if not issubclass(type(args), tuple):
            args = tuple(args)
        for arg in args:
            if type(arg) == Density:
                self.set_density(arg)
            elif type(arg) == Dataset:
                self.data.append(arg)
            elif type(arg) == Lin or type(arg) == Fol or type(arg) == Pole:
                self.data.append(Dataset(arg))
            elif type(arg) == Ortensor:
                for v in arg.eigenlins:
                    self.data.append(v)
            else:
                raise Exception('Wrong argument! '+type(arg) +
                                ' cannot be plotted as linear feature.')

    def set_density(self, density):
        """Nastavi density grid"""
        if type(density) == Density or density == None:
            self.density = density

    def show(self):
        """Draw figure"""
        plt.ion()
        # test if closed
        if not plt._pylab_helpers.Gcf.figs.values():
            self.fig = plt.figure()
            self.ax = self.fig.add_subplot(111)
        # now ok
        self.ax.cla()
        self.ax.set_aspect('equal')
        self.ax.set_autoscale_on(False)
        self.ax.axis([-1.05, 1.05, -1.05, 1.05])
        self.ax.set_axis_off()

        # Projection circle
        self.ax.text(0, 1.02, 'N', ha='center', fontsize=16)
        self.ax.add_artist(plt.Circle((0, 0), 1, color='w', zorder=0))
        TH = np.linspace(0, 360, 361)
        self.ax.plot(sind(TH), cosd(TH), 'k')

        #density grid
        if self.density:
            cs = self.ax.tricontourf(self.density.triang, self.density.density,
                                     self.nc, cmap=self.cm, zorder=1)
            self.ax.tricontour(self.density.triang, self.density.density,
                               self.nc, colors='k', zorder=1)

        #grid
        if self.grid:
            grds = list(range(10, 100, 10)) + list(range(-80, 0, 10))
            a = Lin(0, 0)
            for dip in grds:
                l = Lin(0, dip)
                gc = map(l.rotate, 91*[a], np.linspace(-89.99, 89.99, 91))
                x, y = np.array([r.getxy() for r in gc]).T
                self.ax.plot(x, y, 'k:')
            for dip in grds:
                a = Fol(90, dip)
                l = Lin(90, dip)
                gc = map(l.rotate, 81*[a], np.linspace(-80, 80, 81))
                x, y = np.array([r.getxy() for r in gc]).T
                self.ax.plot(x, y, 'k:')

        # init labels
        handles = []
        labels = []

        # plot data
        for arg in self.data:
            #fol great circle
            dd = arg.getfols()
            if dd:
                for d in dd:
                    l = Lin(*d.dd)
                    gc = map(l.rotate, 91*[d], np.linspace(-89.99, 89.99, 91))
                    x, y = np.array([r.getxy() for r in gc]).T
                    h = self.ax.plot(x, y, color=arg.color, zorder=2, **arg.lines)
                handles.append(h[0])
                labels.append('S ' + arg.name)
            #lin point
            dd = arg.getlins()
            if dd:
                for d in dd:
                    x, y = d.getxy()
                    h = self.ax.scatter(x, y, color=arg.color, zorder=4, **arg.points)
                handles.append(h)
                labels.append('L ' + arg.name)
            #pole point
            dd = arg.getpoles()
            if dd:
                for d in dd:
                    x, y = d.getxy()
                    h = self.ax.scatter(x, y, color=arg.color, zorder=3, **arg.poles)
                handles.append(h)
                labels.append('P ' + arg.name)
        # legend
        if handles:
            self.ax.legend(handles, labels, bbox_to_anchor=(1.03, 1), loc=2,
                           borderaxespad=0., numpoints=1, scatterpoints=1)
        #density grid contours
        if self.density:
            divider = make_axes_locatable(self.ax)
            cax = divider.append_axes("left", size="5%", pad=0.5)
            cb = plt.colorbar(cs, cax=cax)
            # modify tick labels
            lbl = [item.get_text()+'S' for item in cb.ax.get_yticklabels()]
            lbl[lbl.index(next(l for l in lbl if l.startswith('0')))] = 'E'
            cb.set_ticklabels(lbl)
        #finish
        plt.subplots_adjust(left=0.02, bottom=0.05, right=0.78, top=0.95)
        self.fig.canvas.draw()
        plt.show()
        plt.ioff()

    def savefig(self, filename='schmidtnet.pdf'):
        plt.savefig(filename)

def fixpair(f, l):
    """Upraví měření foliace a lineace, tak aby lineace ležela ve foliaci::

        fok,lok = fixpair(f,l)
    """
    ax = f ** l
    ang = (Vec3(l).angle(f) - 90)/2
    return Vec3(f).rotate(ax, ang).asfol(), Vec3(l).rotate(ax, -ang).aslin()


def readcsv(fname, planar=0, acol=1, icol=2, name='Default', color='blue'):
    """Nacte data z csv souboru do datasetu"""
    import csv
    with open(fname, 'rb') as csvfile:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(csvfile.read(1024))
        csvfile.seek(0)
        d = Dataset(name=name, color=color)
        reader = csv.reader(csvfile, dialect)
        if sniffer.has_header:
            reader.next()
        for row in reader:
            if planar:
                d.append(Fol(float(row[acol-1]), float(row[icol-1])))
            else:
                d.append(Lin(float(row[acol-1]), float(row[icol-1])))
        return d


def rose(a, bins=13, **kwargs):
    """vykresli ružicový histogram uhlu"""
    if isinstance(a, Dataset):
        a, _ = a.dd
    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('N')
    arad = a * np.pi / 180
    erad = np.linspace(0, 360, bins) * np.pi / 180
    plt.hist(arad, bins=erad, **kwargs)


if __name__ == "__main__":
    d = Dataset([Fol(0, 60),
                 Fol(90, 60),
                 Fol(180, 60),
                 Fol(270, 60)],
                name='apsg')
    c = Density(d)
    s = SchmidtNet(c, d)