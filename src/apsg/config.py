# Default module settings.

apsg_conf = dict(
    notation="dd",  # notation geological measurements (dd or rhr)
    vec2geo=False,  # repr Vector3 using notation
    ndigits=3,  # Round to ndigits in repr
    figsize=(8, 6),  # Default figure size
    stereonet_default_kwargs=dict(
        kind="equal-area",
        overlay_position=(0, 0, 0, 0),
        rotate_data=False,
        minor_ticks=None,
        major_ticks=None,
        overlay=True,
        overlay_step=15,
        overlay_resolution=181,
        clip_pole=15,
        hemisphere="lower",
        grid_type="gss",
        grid_n=3000,
    ),
    stereonet_default_point_kwargs=dict(
        alpha=None, color=None, mec=None, mfc=None, ls="none", marker="o", mew=1, ms=6,
    ),
    stereonet_default_pole_kwargs=dict(
        alpha=None, color=None, mec=None, mfc=None, ls="none", marker="o", mew=1, ms=6,
    ),
    stereonet_default_vector_kwargs=dict(
        alpha=None, color=None, mec=None, mfc=None, ls="none", marker="o", mew=2, ms=6,
    ),
    stereonet_default_great_circle_kwargs=dict(
        alpha=None, color=None, ls="-", lw=1.5, mec=None, mew=1, mfc=None, ms=2,
    ),
    stereonet_default_arc_kwargs=dict(
        alpha=None, color=None, ls="-", lw=1, mec=None, mew=1, mfc=None, ms=2,
    ),
    stereonet_default_scatter_kwargs=dict(
        alpha=None,
        s=None,
        c=None,
        linewidths=1.5,
        marker=None,
        cmap=None,
        legend=False,
        num="auto",
    ),
    stereonet_default_cone_kwargs=dict(
        alpha=None, color=None, ls="-", lw=1.5, mec=None, mew=1, mfc=None, ms=2,
    ),
    stereonet_default_pair_kwargs=dict(
        alpha=None,
        color=None,
        ls="-",
        lw=1.5,
        mec=None,
        mew=1,
        mfc=None,
        ms=4,
        line_marker="o",
    ),
    stereonet_default_fault_kwargs=dict(
        alpha=None, color=None, ls="-", lw=1.5, mec=None, mew=1, mfc=None, ms=2,
    ),
    stereonet_default_hoeppner_kwargs=dict(
        alpha=None, color=None, mec=None, mfc=None, ls="none", marker="o", mew=1, ms=5,
    ),
    stereonet_default_quiver_kwargs=dict(
        color=None, width=2, headwidth=5, pivot="mid", units="dots",
    ),
    stereonet_default_contourf_kwargs=dict(
        alpha=None,
        antialiased=True,
        cmap="Greys",
        levels=6,
        clines=True,
        linewidths=1,
        linestyles=None,
        colorbar=False,
        trim=True,
        sigma=None,
    ),
    roseplot_default_kwargs=dict(
        bins=36,
        axial=True,
        density=True,
        arrowness=0.95,
        rwidth=1,
        scaled=False,
        kappa=250,
        pdf_res=901,
        title=None,
        grid=True,
        grid_kw=dict(),
    ),
    roseplot_default_bar_kwargs=dict(
        alpha=None, color=None, ec=None, fc=None, ls="-", lw=1.5, legend=False,
    ),
    roseplot_default_pdf_kwargs=dict(
        alpha=None, color=None, ec=None, fc=None, ls="-", lw=1.5, legend=False,
    ),
    roseplot_default_muci_kwargs=dict(
        confidence_level=95, alpha=None, color="r", ls="-", lw=1.5, n_resamples=9999,
    ),
    fabricplot_default_kwargs=dict(
        ticks=True,
        n_ticks=10,
        tick_size=0.2,
        margin=0.05,
        grid=True,
        grid_color="k",
        grid_style=":",
        title=None,
    ),
    fabricplot_default_point_kwargs=dict(
        alpha=None, color=None, mec=None, mfc=None, ls="none", marker="o", mew=1, ms=8,
    ),
    fabricplot_default_path_kwargs=dict(
        alpha=None, color=None, ls="-", lw=1.5, marker=None, mec=None, mew=1, mfc=None, ms=6,
    ),
)
