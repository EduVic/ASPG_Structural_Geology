# -*- coding: utf-8 -*-

"""
API to read data from PySDB database
"""

import sqlite3
import os.path
from apsg.core import Fol, Lin, Group


__all__ = ("SDB",)


class SDB(object):
    """PySDB database access class"""

    _SELECT = """SELECT sites.name as name, sites.x_coord as x,
    sites.y_coord as y, units.name as unit, structdata.azimuth as azimuth,
    structdata.inclination as inclination, structype.structure as structure,
    structype.planar as planar, structdata.description as description,
    GROUP_CONCAT(tags.name) AS tags
    FROM structdata
    INNER JOIN sites ON structdata.id_sites=sites.id
    INNER JOIN structype ON structype.id = structdata.id_structype
    INNER JOIN units ON units.id = sites.id_units
    LEFT OUTER JOIN tagged ON structdata.id = tagged.id_structdata
    LEFT OUTER JOIN tags ON tags.id = tagged.id_tags"""

    _SITE_SELECT = """SELECT sites.name as name, units.name as unit,
    sites.x_coord as x, sites.y_coord as y, sites.description as description
    FROM sites
    INNER JOIN units ON units.id = sites.id_units
    ORDER BY sites.name"""

    def __new__(cls, db):
        assert os.path.isfile(db), 'Database does not exists.'
        cls.conn = sqlite3.connect(db)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("pragma encoding='UTF-8'")
        cls.conn.execute(SDB._SELECT + " LIMIT 1")
        return super(SDB, cls).__new__(cls)

    def __repr__(self):
        return "PySDB database version: {}".format(self.meta("version"))

    def meta(self, name, val=None, delete=False):
        if delete:
            try:
                self.conn.execute("DELETE FROM meta WHERE name=?", (name,))
                self.conn.commit()
            except sqlite3.OperationalError:
                self.conn.rollback()
                print("Metadata '{}' not deleted.".format(name))
                raise
        elif val is None:
            if name == "crs":  # keep compatible with old sdb files
                val = self.conn.execute(
                    "SELECT value FROM meta WHERE name='crs'"
                ).fetchall()
                if not val:
                    name = "proj4"
            res = self.conn.execute(
                "SELECT value FROM meta WHERE name=?", (name,)
            ).fetchall()
            if res:
                return res[0][0]
            else:
                raise ValueError("SDB: Metadata '{}' does not exists".format(name))
        else:
            try:
                exval = self.conn.execute(
                    "SELECT value FROM meta WHERE name=?", (name,)
                ).fetchall()
                if not exval:
                    self.conn.execute(
                        "INSERT INTO meta (name,value) VALUES (?,?)", (name, val)
                    )
                else:
                    self.conn.execute(
                        "UPDATE meta SET value = ? WHERE name = ?", (val, name)
                    )
                self.conn.commit()
            except sqlite3.OperationalError:
                self.conn.rollback()
                print("Metadata '{}' not updated.".format(name))
                raise

    def info(self, report='basic'):
        lines = []
        if report == 'basic':
            lines.append("PySDB database version: {}".format(self.meta("version")))
            lines.append("PySDB database CRS: {}".format(self.meta("crs")))
            lines.append("PySDB database created: {}".format(self.meta("created")))
            lines.append("PySDB database updated: {}".format(self.meta("updated")))
            lines.append("Number of sites: {}".format(len(self.sites())))
            lines.append("Number of units: {}".format(len(self.units())))
            lines.append("Number of structures: {}".format(len(self.structures())))
            r = self.execsql(self._make_select())
            lines.append("Number of measurements: {}".format(len(r)))
        elif report == 'data':
            for s in self.structures():
                r = self.execsql(self._make_select(structs=s))
                if len(r) > 0:
                    lines.append("Number of {} measurements: {}".format(s, len(r)))
        elif report == 'tags':
            for s in self.structures():
                r = self.execsql(self._make_select(tags=s))
                if len(r) > 0:
                    lines.append("{} measurements tagged as {}.".format(len(r), s))
        else:
            lines.append('No report.')

        return '\n'.join(lines)

    def _make_select(self, structs=None, sites=None, units=None, tags=None):
        w = []
        if structs:
            if isinstance(structs, str):
                w.append("structype.structure='%s'" % structs)
            elif isinstance(structs, (list, tuple)):
                u = " OR ".join(
                    ["structype.structure='{}'".format(struct) for struct in structs]
                )
                w.append("(" + u + ")")
            else:
                raise ValueError("Keyword structs must be list or string.")
        if sites:
            if isinstance(sites, str):
                w.append("sites.name='{}'".format(sites))
            elif isinstance(sites, (list, tuple)):
                u = " OR ".join(["sites.name='{}'".format(site) for site in sites])
                w.append("(" + u + ")")
            else:
                raise ValueError("Keyword sites must be list or string.")
        if units:
            if isinstance(units, str):
                w.append("unit='{}'".format(units))
            elif isinstance(units, (list, tuple)):
                u = " OR ".join(["unit='{}'".format(unit) for unit in units])
                w.append("(" + u + ")")
            else:
                raise ValueError("Keyword units must be list or string.")
        if tags:
            if isinstance(tags, str):
                tagw = ["tags LIKE '%{}%'".format(tags)]
            elif isinstance(tags, (list, tuple)):
                u = " AND ".join(["tags LIKE '%{}%'".format(tag) for tag in tags])
                tagw = ["({})".format(u)]
            else:
                raise ValueError("Keyword tags must be list or string.")
            insel = SDB._SELECT
            if w:
                insel += " WHERE {} GROUP BY structdata.id".format(" AND ".join(w))
            else:
                insel += " GROUP BY structdata.id"
            sel = "SELECT * FROM ({}) WHERE {}".format(insel, " AND ".join(tagw))
        else:
            sel = SDB._SELECT
            if w:
                sel += " WHERE {} GROUP BY structdata.id".format(" AND ".join(w))
            else:
                sel += " GROUP BY structdata.id"
        return sel

    def execsql(self, sql):
        return self.conn.execute(sql).fetchall()

    def structures(self, **kwargs):
        """Return list of structures in data. For kwargs see group method."""
        if kwargs:
            dtsel = self._make_select(**kwargs)
            res = set([el["structure"] for el in self.execsql(dtsel)])
            return sorted(list(res))
        else:
            dtsel = "SELECT structure FROM structype ORDER BY pos"
            return [el['structure'] for el in self.execsql(dtsel)]

    def sites(self, **kwargs):
        """Return list of sites in data. For kwargs see group method."""
        if kwargs:
            dtsel = self._make_select(**kwargs)
            res = set([el["name"] for el in self.execsql(dtsel)])
            return sorted(list(res))
        else:
            dtsel = "SELECT name FROM sites ORDER BY id"
            return [el['name'] for el in self.execsql(dtsel)]

    def units(self, **kwargs):
        """Return list of units in data. For kwargs see group method."""
        if kwargs:
            dtsel = self._make_select(**kwargs)
            res = set([el["unit"] for el in self.execsql(dtsel)])
            return sorted(list(res))
        else:
            dtsel = "SELECT name FROM units ORDER BY pos"
            return [el['name'] for el in self.execsql(dtsel)]

    def tags(self, **kwargs):
        """Return list of tags in data. For kwargs see group method."""
        if kwargs:
            dtsel = self._make_select(**kwargs)
            tags = [el["tags"] for el in self.execsql(dtsel) if el["tags"] is not None]
            return sorted(list(set(",".join(tags).split(","))))
        else:
            dtsel = "SELECT name FROM tags ORDER BY pos"
            return [el['name'] for el in self.execsql(dtsel)]

    def is_planar(self, struct):
        tpsel = "SELECT planar FROM structype WHERE structure='{}'".format(struct)
        res = self.execsql(tpsel)
        return res[0][0] == 1

    def group(self, struct, **kwargs):
        """Method to retrieve data from SDB database to apsg.Group

        Args:
          struct:  name of structure to retrieve

        Keyword Args:
          sites: name or list of names of sites to retrieve from
          units: name or list of names of units to retrieve from
          tags:  tag or list of tags to retrieve

        """
        dtsel = self._make_select(structs=struct, **kwargs)
        sel = self.execsql(dtsel)
        if sel:
            if self.is_planar(struct):
                res = Group(
                    [Fol(el["azimuth"], el["inclination"]) for el in sel], name=struct,
                )
            else:
                res = Group(
                    [Lin(el["azimuth"], el["inclination"]) for el in sel], name=struct,
                )
            return res
        else:
            raise ValueError("No structures found using provided criteria.")
