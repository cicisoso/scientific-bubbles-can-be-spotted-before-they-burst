"""Shared publication style for all figures (Python/matplotlib backend, Nature-style)."""
import sys, os, json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.transforms import ScaledTranslation
sys.path.insert(0, os.path.expanduser('~/.claude/skills/nature-figure/scripts'))
try:
    from audit_panel_alignment import require_matplotlib_panel_alignment   # render-time panel-alignment gate (nature-figure QA scripts)
except ImportError:
    require_matplotlib_panel_alignment = None

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'
mpl.rcParams.update({
    'pdf.fonttype': 42, 'ps.fonttype': 42,
    'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
    'legend.fontsize': 6.5, 'axes.spines.right': False, 'axes.spines.top': False, 'axes.linewidth': 0.6,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'legend.frameon': False, 'lines.linewidth': 1.2, 'axes.unicode_minus': False,
})
PALETTE = {
    'blue_main': '#0F4D92', 'blue_secondary': '#3775BA', 'teal': '#42949E', 'red_strong': '#B64342',
    'red_2': '#E9A6A1', 'green_3': '#8BCF8B', 'violet': '#9A4D8E', 'gold': '#D9A400',
    'neutral_light': '#CFCECE', 'neutral_mid': '#767676', 'neutral_dark': '#4D4D4D', 'neutral_black': '#272727',
}
CLOCK = {'publication': PALETTE['neutral_mid'], 'acceptance': PALETTE['teal'], 'submission': PALETTE['blue_main']}
RETRACT = PALETTE['red_strong']
MM = 1/25.4

def add_panel_label(ax, label, x=0, y=1, x_offset_pt=-6, y_offset_pt=3, fontsize=8):
    off = ScaledTranslation(x_offset_pt/72, y_offset_pt/72, ax.figure.dpi_scale_trans)
    ax.text(x, y, label, transform=ax.transAxes + off, fontsize=fontsize, fontweight='bold', ha='left', va='bottom')
    if label.isupper():   # Science-style capital labels: register an undrawn lowercase twin so the alignment auditor can find the anchor
        ax.text(x, y, label.lower(), transform=ax.transAxes + off, fontsize=fontsize, fontweight='bold', ha='left', va='bottom', visible=False)

def anchor_only(ax, x_offset_pt=-6, y_offset_pt=3, fontsize=8):
    """Sub-panels that share one printed label (small multiples): register an undrawn anchor so the alignment auditor can still compare them."""
    off = ScaledTranslation(x_offset_pt/72, y_offset_pt/72, ax.figure.dpi_scale_trans)
    ax.text(0, 1, 'a', transform=ax.transAxes + off, fontsize=fontsize, fontweight='bold', ha='left', va='bottom', visible=False)

def finalize(fig, stem, single_panel=False, exemptions=None):
    """Alignment gate + export (SVG/PDF primary, PNG preview)."""
    fig.canvas.draw()
    if not single_panel and require_matplotlib_panel_alignment is None:
        print('warning: audit_panel_alignment not installed; alignment gate skipped for', stem)
    if not single_panel and require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=f'{stem}.alignment.json', overlay_svg=f'{stem}.alignment.svg',
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True,
                                           **({'exemptions': exemptions} if exemptions else {}))
    fig.savefig(f'{stem}.pdf')
    fig.savefig(f'{stem}.svg')
    fig.savefig(f'{stem}.png', dpi=300)
    print('saved', stem)

def loadj(p):
    return json.load(open(p))
