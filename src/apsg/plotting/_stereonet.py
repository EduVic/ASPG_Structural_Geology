# -*- coding: utf-8 -*-

# import warnings
import pickle

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# from matplotlib import MatplotlibDeprecationWarning

from apsg.config import apsg_conf
from apsg.math._vector import Vector3
from apsg.feature._geodata import Lineation, Foliation, Pair, Fault, Cone
from apsg.feature._container import (
    FeatureSet,
    Vector3Set,
    LineationSet,
    FoliationSet,
    PairSet,
    FaultSet,
)
from apsg.feature import feature_from_json
from apsg.plotting._stereogrid import StereoGrid
from apsg.feature._tensor3 import OrientationTensor3
from apsg.plotting._projection import EqualAreaProj, EqualAngleProj
from apsg.plotting._plot_artists import StereoNetArtistFactory

__all__ = ["StereoNet"]


# Ignore `matplotlib`s deprecation warnings.
# warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)


class StereoNet:
    """
    Plot features on stereographic projection

    Keyword Args:
        title (str): figure title. Default None.
        kind (str): "equal-area" or "equal-angle". "schmidt", "earea" or "wulff", "eangle" is
          also valid. Default is "equal-area"
        hemisphere (str): "lower" or "upper". Default is "lower"
        overlay_position (tuple or Pair): Position of overlay X, Y, Z given by Pair. X is direction
          of linear element, Z is normal to planar. Default is (0, 0, 0, 0)
        rotate_data (bool): Whether plotted data should be rotated together with overlay.
          Default False
        minor_ticks (None or float): Default None
        major_ticks (None or float): Default None
        overlay (bool): Whether to show overlay. Default is True
        overlay_step (float): Grid step of overlay. Default 15
        overlay_resolution (float): Resolution of overlay. Default 181
        clip_pole (float): Clipped cone around poles. Default 15
        grid_type (str): Type of contouring grid "gss" or "sfs". Default "gss"
        grid_n (int): Number of counting points in grid. Default 3000
        tight_layout (bool): Matplotlib figure tight_layout. Default False
    """

    def __init__(self, **kwargs):
        self._kwargs = apsg_conf["stereonet_default_kwargs"].copy()
        self._kwargs.update((k, kwargs[k]) for k in self._kwargs.keys() & kwargs.keys())
        self._kwargs["title"] = kwargs.get("title", None)
        if self._kwargs["kind"].lower() in ["equal-area", "schmidt", "earea"]:
            self.proj = EqualAreaProj(**self._kwargs)
        elif self._kwargs["kind"].lower() in ["equal-angle", "wulff", "eangle"]:
            self.proj = EqualAngleProj(**self._kwargs)
        else:
            raise TypeError("Only 'Equal-area' and 'Equal-angle' implemented")
        self.angles_gc = np.linspace(
            -90 + 1e-7, 90 - 1e-7, int(self.proj.overlay_resolution / 2)
        )
        self.angles_sc = np.linspace(
            -180 + 1e-7, 180 - 1e-7, self.proj.overlay_resolution
        )
        self.grid = StereoGrid(**self._kwargs)
        self.clear()

    def clear(self):
        self._artists = []

    def _draw_layout(self):
        # overlay
        if self._kwargs["overlay"]:
            ov = self.proj.get_grid_overlay()
            for dip, d in ov["lat_e"].items():
                self.ax.plot(d["x"], d["y"], "k:", lw=1)
            for dip, d in ov["lat_w"].items():
                self.ax.plot(d["x"], d["y"], "k:", lw=1)
            for dip, d in ov["lon_n"].items():
                self.ax.plot(d["x"], d["y"], "k:", lw=1)
            for dip, d in ov["lon_s"].items():
                self.ax.plot(d["x"], d["y"], "k:", lw=1)
            if ov["main_xz"]:
                self.ax.plot(ov["main_xz"]["x"], ov["main_xz"]["y"], "k:", lw=1)
            if ov["main_yz"]:
                self.ax.plot(ov["main_yz"]["x"], ov["main_yz"]["y"], "k:", lw=1)
            if ov["main_xy"]:
                self.ax.plot(ov["main_xy"]["x"], ov["main_xy"]["y"], "k:", lw=1)
            if ov["polehole_n"]:
                self.ax.plot(ov["polehole_n"]["x"], ov["polehole_n"]["y"], "k", lw=1)
            if ov["polehole_s"]:
                self.ax.plot(ov["polehole_s"]["x"], ov["polehole_s"]["y"], "k", lw=1)
            if ov["main_x"]:
                self.ax.plot(ov["main_x"]["x"], ov["main_x"]["y"], "k", lw=2)
            if ov["main_y"]:
                self.ax.plot(ov["main_y"]["x"], ov["main_y"]["y"], "k", lw=2)
            if ov["main_z"]:
                self.ax.plot(ov["main_z"]["x"], ov["main_z"]["y"], "k", lw=2)

        # Projection circle frame
        theta = np.linspace(0, 2 * np.pi, 200)
        self.ax.plot(np.cos(theta), np.sin(theta), "k", lw=2)
        # Minor ticks
        if self._kwargs["minor_ticks"] is not None:
            ticks = np.array([1, 1.02])
            theta = np.arange(0, 2 * np.pi, np.radians(self._kwargs["minor_ticks"]))
            self.ax.plot(
                np.outer(ticks, np.cos(theta)),
                np.outer(ticks, np.sin(theta)),
                "k",
                lw=1,
            )
        # Major ticks
        if self._kwargs["major_ticks"] is not None:
            ticks = np.array([1, 1.03])
            theta = np.arange(0, 2 * np.pi, np.radians(self._kwargs["major_ticks"]))
            self.ax.plot(
                np.outer(ticks, np.cos(theta)),
                np.outer(ticks, np.sin(theta)),
                "k",
                lw=1.5,
            )
        # add clipping circle
        self.primitive = Circle(
            (0, 0),
            radius=1,
            edgecolor="black",
            fill=False,
            clip_box="None",
            label="_nolegend_",
        )
        self.ax.add_patch(self.primitive)

    def _plot_artists(self):
        for artist in self._artists:
            plot_method = getattr(self, artist.stereonet_method)
            plot_method(*artist.args, **artist.kwargs)

    def to_json(self):
        artists = [artist.to_json() for artist in self._artists]
        return dict(kwargs=self._kwargs, artists=artists)

    @classmethod
    def from_json(cls, json_dict):
        s = cls(**json_dict["kwargs"])
        s._artists = [
            stereonetartist_from_json(artist) for artist in json_dict["artists"]
        ]
        return s

    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self.to_json(), f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            data = pickle.load(f)
        return cls.from_json(data)

    def init_figure(self):
        self.fig = plt.figure(
            0,
            figsize=apsg_conf["figsize"],
            dpi=apsg_conf["dpi"],
            facecolor=apsg_conf["facecolor"],
        )
        if hasattr(self.fig.canvas.manager, "set_window_title"):
            self.fig.canvas.manager.set_window_title(self.proj.netname)

    def _render(self):
        self.ax = self.fig.add_subplot()
        self.ax.set_aspect(1)
        self.ax.set_axis_off()
        self._draw_layout()
        self._plot_artists()
        self.ax.set_xlim(-1.05, 1.05)
        self.ax.set_ylim(-1.05, 1.05)
        h, labels = self.ax.get_legend_handles_labels()
        if h:
            self.ax.legend(
                h,
                labels,
                bbox_to_anchor=(1.05, 1),
                prop={"size": 11},
                loc="upper left",
                borderaxespad=0,
                scatterpoints=1,
                numpoints=1,
            )
        if self._kwargs["title"] is not None:
            self.fig.suptitle(self._kwargs["title"])
        if self._kwargs["tight_layout"]:
            self.fig.tight_layout()

    def render(self):
        if not hasattr(self, "fig"):
            self.init_figure()
        else:
            self.fig.clear()
        self._render()

    def show(self):
        plt.close(0)  # close previously rendered figure
        self.init_figure()
        self._render()
        plt.show()

    def savefig(self, filename="stereonet.png", **kwargs):
        self.render()
        self.fig.savefig(filename, **kwargs)
        plt.close(0)

    ########################################
    # PLOTTING METHODS                     #
    ########################################

    def line(self, *args, **kwargs):
        """Plot linear feature(s) as point(s)"""
        try:
            artist = StereoNetArtistFactory.create_point(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def pole(self, *args, **kwargs):
        """Plot pole of planar feature(s) as point(s)"""
        try:
            artist = StereoNetArtistFactory.create_pole(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def vector(self, *args, **kwargs):
        """Plot vector feature(s) as point(s),
        filled on lower and open on upper hemisphere."""
        try:
            artist = StereoNetArtistFactory.create_vector(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def scatter(self, *args, **kwargs):
        """Plot vector-like feature(s) as point(s) using scatter"""
        try:
            artist = StereoNetArtistFactory.create_scatter(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def great_circle(self, *args, **kwargs):
        """Plot planar feature(s) as great circle(s)"""
        try:
            artist = StereoNetArtistFactory.create_great_circle(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def arc(self, *args, **kwargs):
        """Plot arc bewtween two vectors along great circle(s)"""
        try:
            artist = StereoNetArtistFactory.create_arc(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def cone(self, *args, **kwargs):
        """Plot small circle(s) with given angle(s)"""
        try:
            artist = StereoNetArtistFactory.create_cone(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def pair(self, *args, **kwargs):
        """Plot pair feature(s) as great circle and point"""
        try:
            artist = StereoNetArtistFactory.create_pair(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def fault(self, *args, **kwargs):
        """Plot fault feature(s) as great circle and point"""
        try:
            artist = StereoNetArtistFactory.create_fault(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def hoeppner(self, *args, **kwargs):
        """Plot a fault-and-striae as in tangent lineation plot - Hoeppner plot."""
        try:
            artist = StereoNetArtistFactory.create_hoeppner(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def arrow(self, *args, **kwargs):
        """Plot arrows at position of first argument
        and oriented in direction of second"""
        try:
            artist = StereoNetArtistFactory.create_arrow(*args, **kwargs)
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    def contour(self, *args, **kwargs):
        """Plot filled contours."""
        try:
            artist = StereoNetArtistFactory.create_contour(*args, **kwargs)
            # ad-hoc density calculation needed to access correct grid properties
            if len(args) > 0:
                self.grid.calculate_density(
                    args[0], sigma=kwargs.get("sigma"), trim=kwargs.get("trim")
                )
            self._artists.append(artist)
        except TypeError as err:
            print(err)

    ########################################
    # PLOTTING ROUTINES                    #
    ########################################

    def _line(self, *args, **kwargs):
        x_lower, y_lower = self.proj.project_data(*np.vstack(args).T)
        x_upper, y_upper = self.proj.project_data(*(-np.vstack(args).T))
        handles = self.ax.plot(
            np.hstack((x_lower, x_upper)), np.hstack((y_lower, y_upper)), **kwargs
        )
        for h in handles:
            h.set_clip_path(self.primitive)
        return handles

    def _vector(self, *args, **kwargs):
        x_lower, y_lower, x_upper, y_upper = self.proj.project_data_antipodal(
            *np.vstack(args).T
        )
        if len(x_lower) > 0:
            handles = self.ax.plot(x_lower, y_lower, **kwargs)
            for h in handles:
                h.set_clip_path(self.primitive)
            u_kwargs = kwargs.copy()
            u_kwargs["label"] = "_upper"
            u_kwargs["mec"] = h.get_color()
            u_kwargs["mfc"] = "none"
            handles = self.ax.plot(x_upper, y_upper, **u_kwargs)
            for h in handles:
                h.set_clip_path(self.primitive)
        else:
            u_kwargs = kwargs.copy()
            u_kwargs["mfc"] = "none"
            handles = self.ax.plot(x_upper, y_upper, **u_kwargs)
            for h in handles:
                h.set_clip_path(self.primitive)
        return handles

    def _great_circle(self, *args, **kwargs):
        X, Y = [], []
        for arg in args:
            if self.proj.rotate_data:
                fdv = arg.transform(self.proj.R).dipvec().transform(self.proj.Ri)
            else:
                fdv = arg.dipvec()
            # iterate
            for fol, dv in zip(np.atleast_2d(arg), np.atleast_2d(fdv)):
                # plot on lower
                x, y = self.proj.project_data(
                    *np.array(
                        [Vector3(dv).rotate(Vector3(fol), a) for a in self.angles_gc]
                    ).T
                )
                X.append(np.hstack((x, np.nan)))
                Y.append(np.hstack((y, np.nan)))
                # plot on upper
                x, y = self.proj.project_data(
                    *np.array(
                        [-Vector3(dv).rotate(Vector3(fol), a) for a in self.angles_gc]
                    ).T
                )
                X.append(np.hstack((x, np.nan)))
                Y.append(np.hstack((y, np.nan)))
        handles = self.ax.plot(np.hstack(X), np.hstack(Y), **kwargs)
        for h in handles:
            h.set_clip_path(self.primitive)
        return handles

    def _arc(self, *args, **kwargs):
        X_lower, Y_lower = [], []
        X_upper, Y_upper = [], []
        antipodal = any([type(arg) is Vector3 for arg in args])
        u_kwargs = kwargs.copy()
        u_kwargs["ls"] = "--"
        u_kwargs["label"] = "_upper"
        for arg1, arg2 in zip(args[:-1], args[1:]):
            steps = max(2, int(arg1.angle(arg2)))
            # plot on lower
            x_lower, y_lower, x_upper, y_upper = self.proj.project_data_antipodal(
                *np.array([arg1.slerp(arg2, t) for t in np.linspace(0, 1, steps)]).T
            )
            X_lower.append(np.hstack((x_lower, np.nan)))
            Y_lower.append(np.hstack((y_lower, np.nan)))
            X_upper.append(np.hstack((x_upper, np.nan)))
            Y_upper.append(np.hstack((y_upper, np.nan)))
        handles = self.ax.plot(np.hstack(X_lower), np.hstack(Y_lower), **kwargs)
        for h in handles:
            h.set_clip_path(self.primitive)
        if antipodal:
            u_kwargs["color"] = h.get_color()
            handles_2 = self.ax.plot(np.hstack(X_upper), np.hstack(Y_upper), **u_kwargs)
            for h in handles_2:
                h.set_clip_path(self.primitive)
        return handles

    def _scatter(self, *args, **kwargs):
        legend = kwargs.pop("legend")
        num = kwargs.pop("num")
        x_lower, y_lower = self.proj.project_data(*np.vstack(args).T)
        mask_lower = ~np.isnan(x_lower)
        x_upper, y_upper, mask_upper = self.proj.project_data(*(-np.vstack(args).T))
        mask_upper = ~np.isnan(x_upper)
        prop = "sizes"
        if kwargs["s"] is not None:
            s = np.atleast_1d(kwargs["s"])
            kwargs["s"] = np.hstack((s[mask_lower], s[mask_upper]))
        if kwargs["c"] is not None:
            c = np.atleast_1d(kwargs["c"])
            kwargs["c"] = np.hstack((c[mask_lower], c[mask_upper]))
            prop = "colors"
        sc = self.ax.scatter(
            np.hstack((x_lower, x_upper)),
            np.hstack((y_lower, y_upper)),
            **kwargs,
        )
        if legend:
            self.ax.legend(
                *sc.legend_elements(prop, num=num),
                bbox_to_anchor=(1.05, 1),
                prop={"size": 11},
                loc="upper left",
                borderaxespad=0,
            )
        sc.set_clip_path(self.primitive)

    # def _cone(self, *args, **kwargs):
    #     X, Y = [], []
    #     # get scalar arguments from kwargs
    #     angles = kwargs.pop("angle")
    #     for axis, angle in zip(np.vstack(args), angles):
    #         if self.proj.rotate_data:
    #             lt = axis.transform(self.proj.R)
    #             azi, dip = Vector3(lt).geo
    #             cl_lower = Vector3(azi, dip + angle).transform(self.proj.Ri)
    #             cl_upper = -Vector3(azi, dip - angle).transform(self.proj.Ri)
    #         else:
    #             lt = axis
    #             azi, dip = Vector3(lt).geo
    #             cl_lower = Vector3(azi, dip + angle)
    #             cl_upper = -Vector3(azi, dip - angle)
    #         # plot on lower
    #         x, y = self.proj.project_data(
    #             *np.array([cl_lower.rotate(lt, a) for a in self.angles_sc]).T
    #         )
    #         X.append(np.hstack((x, np.nan)))
    #         Y.append(np.hstack((y, np.nan)))
    #         # plot on upper
    #         x, y = self.proj.project_data(
    #             *np.array([cl_upper.rotate(-lt, a) for a in self.angles_sc]).T
    #         )
    #         X.append(np.hstack((x, np.nan)))
    #         Y.append(np.hstack((y, np.nan)))
    #     handles = self.ax.plot(np.hstack(X), np.hstack(Y), **kwargs)
    #     for h in handles:
    #         h.set_clip_path(self.primitive)
    #     return handles

    def _cone(self, *args, **kwargs):
        X, Y = [], []
        # get scalar arguments from kwargs
        for arg in args:
            if issubclass(type(arg), Cone):
                cones = [arg]
            else:
                cones = arg
            for c in cones:
                # plot on lower
                angles = np.linspace(0, c.revangle, max(2, abs(int(c.revangle))))
                x, y = self.proj.project_data(
                    *np.array([c.secant.rotate(c.axis, a) for a in angles]).T
                )
                X.append(np.hstack((x, np.nan)))
                Y.append(np.hstack((y, np.nan)))
                # plot on upper
                x, y = self.proj.project_data(
                    *np.array([-c.secant.rotate(c.axis, a) for a in angles]).T
                )
                X.append(np.hstack((x, np.nan)))
                Y.append(np.hstack((y, np.nan)))
        handles = self.ax.plot(np.hstack(X), np.hstack(Y), **kwargs)
        for h in handles:
            h.set_clip_path(self.primitive)
        return handles

    def _pair(self, *args, **kwargs):
        line_marker = kwargs.pop("line_marker")
        h = self._great_circle(*[arg.fol for arg in args], **kwargs)
        self._line(
            *[arg.lin for arg in args],
            marker=line_marker,
            ls="none",
            mfc=h[0].get_color(),
            mec=h[0].get_color(),
            ms=kwargs.get("ms"),
        )

    def _fault(self, *args, **kwargs):
        h = self._great_circle(*[arg.fol for arg in args], **kwargs)
        quiver_kwargs = apsg_conf["stereonet_default_quiver_kwargs"]
        quiver_kwargs["pivot"] = "tail"
        quiver_kwargs["color"] = h[0].get_color()
        for arg in args:
            self._arrow(arg.lin, sense=arg.sense, **quiver_kwargs)

    def _hoeppner(self, *args, **kwargs):
        h = self._line(*[arg.fol for arg in args], **kwargs)
        quiver_kwargs = apsg_conf["stereonet_default_quiver_kwargs"]
        quiver_kwargs["color"] = h[0].get_color()
        for arg in args:
            self._arrow(arg.fol, arg.lin, sense=arg.sense, **quiver_kwargs)

    def _arrow(self, *args, **kwargs):
        x_lower, y_lower = self.proj.project_data(*np.vstack(np.atleast_2d(args[0])).T)
        x_upper, y_upper = self.proj.project_data(
            *(-np.vstack(np.atleast_2d(args[0])).T)
        )
        x = np.hstack((x_lower, x_upper))
        x = x[~np.isnan(x)]
        y = np.hstack((y_lower, y_upper))
        y = y[~np.isnan(y)]
        if len(args) > 1:
            x_lower, y_lower = self.proj.project_data(
                *np.vstack(np.atleast_2d(args[1])).T
            )
            x_upper, y_upper = self.proj.project_data(
                *(-np.vstack(np.atleast_2d(args[1])).T)
            )
            dx = np.hstack((x_lower, x_upper))
            dx = dx[~np.isnan(dx)]
            dy = np.hstack((y_lower, y_upper))
            dy = dy[~np.isnan(dy)]
        else:
            dx, dy = x, y
        mag = np.hypot(dx, dy)
        sense = np.atleast_1d(kwargs.pop("sense"))
        u, v = sense * dx / mag, sense * dy / mag
        h = self.ax.quiver(x, y, u, v, **kwargs)
        h.set_clip_path(self.primitive)

    def _contour(self, *args, **kwargs):
        sigma = kwargs.pop("sigma")
        trim = kwargs.pop("trim")
        colorbar = kwargs.pop("colorbar")
        _ = kwargs.pop("label")
        clines = kwargs.pop("clines")
        linewidths = kwargs.pop("linewidths")
        linestyles = kwargs.pop("linestyles")
        show_data = kwargs.pop("show_data")
        data_kwargs = kwargs.pop("data_kwargs")
        if not self.grid.calculated:
            if len(args) > 0:
                self.grid.calculate_density(args[0], sigma=sigma, trim=trim)
            else:
                return None
        dcgrid = np.asarray(self.grid.grid).T
        X, Y = self.proj.project_data(*dcgrid, clip_inside=False)
        cf = self.ax.tricontourf(X, Y, self.grid.values, **kwargs)
        for collection in cf.collections:
            collection.set_clip_path(self.primitive)
        if clines:
            kwargs["cmap"] = None
            kwargs["colors"] = "k"
            kwargs["linewidths"] = linewidths
            kwargs["linestyles"] = linestyles
            cl = self.ax.tricontour(X, Y, self.grid.values, **kwargs)
            for collection in cl.collections:
                collection.set_clip_path(self.primitive)
        if show_data:
            artist = StereoNetArtistFactory.create_point(*args[0], **data_kwargs)
            self._line(*artist.args, **artist.kwargs)
        if colorbar:
            self.fig.colorbar(cf, ax=self.ax, shrink=0.5, anchor=(0.0, 0.3))
        # plt.colorbar(cf, format="%3.2f", spacing="proportional")


def stereonetartist_from_json(obj_json):
    args = tuple([feature_from_json(arg_json) for arg_json in obj_json["args"]])
    return getattr(StereoNetArtistFactory, obj_json["factory"])(
        *args, **obj_json["kwargs"]
    )


def quicknet(*args, **kwargs):
    """
    Function to quickly show or save ``StereoNet`` from args

    Args:
        args: object(s) to be plotted. Instaces of ``Vector3``, ``Foliation``,
            ``Lineation``, ``Pair``, ``Fault``, ``Cone``, ``Vector3Set``,
            ``FoliationSet``, ``LineationSet``, ``PairSet`` or ``FaultSet``.

    Keyword Args:
        savefig (bool): True to save figure. Default `False`
        filename (str): filename for figure. Default `stereonet.png`
        savefig_kwargs (dict): dict passed to ``plt.savefig``
        fol_as_pole (bool): True to plot planar features as poles,
            False for plotting as great circle. Default `True`

    Example:
        >>> l = linset.random_fisher(position=lin(120, 50))
        >>> f = folset.random_fisher(position=lin(300, 40))
        >>> quicknet(f, l, fol_as_pole=False)
    """
    savefig = kwargs.get("savefig", False)
    filename = kwargs.get("filename", "stereonet.png")
    savefig_kwargs = kwargs.get("savefig_kwargs", {})
    fol_as_pole = kwargs.get("fol_as_pole", True)
    s = StereoNet(**kwargs)
    for arg in args:
        if isinstance(arg, Vector3):
            if isinstance(arg, Foliation):
                if fol_as_pole:
                    s.pole(arg)
                else:
                    s.great_circle(arg)
            elif isinstance(arg, Lineation):
                s.line(arg)
            else:
                s.vector(arg)
        elif isinstance(arg, Pair):
            s.pair(arg)
        elif isinstance(arg, Fault):
            s.fault(arg)
        elif isinstance(arg, Cone):
            s.cone(arg)
        elif isinstance(arg, Vector3Set):
            if isinstance(arg, FoliationSet):
                if fol_as_pole:
                    s.pole(arg)
                else:
                    s.great_circle(arg)
            elif isinstance(arg, LineationSet):
                s.line(arg)
            else:
                s.vector(arg)
        elif isinstance(arg, PairSet):
            s.pair(arg)
        elif isinstance(arg, FaultSet):
            s.fault(arg)
        else:
            print(f"{type(arg)} not supported.")
    if savefig:
        s.savefig(filename, **savefig_kwargs)
    else:
        s.show()
