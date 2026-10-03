import matplotlib.cm as cm

# Grab the first two colors from tab10 (same as your first script)
tab10_colors = cm.get_cmap('tab10', 2)

# Centralized styling configuration
EXP_STYLES = {
    "conn40": {
        "label": "40 Connections",
        "color": tab10_colors(0), 
        "linestyle": "--"
    },
    "conn100": {
        "label": "100 Connections",
        "color": tab10_colors(1), 
        "linestyle": "-"
    }
}
