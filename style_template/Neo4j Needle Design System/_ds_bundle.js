/* @ds-bundle: {"format":4,"namespace":"Neo4jNeedleDesignSystem_eb581b","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"CodeBlock","sourcePath":"components/data/CodeBlock.jsx"},{"name":"DataTable","sourcePath":"components/data/DataTable.jsx"},{"name":"GraphLegend","sourcePath":"components/data/GraphLegend.jsx"},{"name":"Banner","sourcePath":"components/feedback/Banner.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"LoadingSpinner","sourcePath":"components/feedback/LoadingSpinner.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"TextInput","sourcePath":"components/forms/TextInput.jsx"},{"name":"Breadcrumbs","sourcePath":"components/navigation/Breadcrumbs.jsx"},{"name":"SideNavigation","sourcePath":"components/navigation/SideNavigation.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"d0b5e6037d5a","components/core/Button.jsx":"f7a2e43f420f","components/core/Card.jsx":"ef72762fb749","components/core/IconButton.jsx":"48b5e3842025","components/core/Tag.jsx":"890080efde27","components/data/CodeBlock.jsx":"8b09ef11cbdc","components/data/DataTable.jsx":"28428784c22f","components/data/GraphLegend.jsx":"4dd6a585c34c","components/feedback/Banner.jsx":"fe6638077ca8","components/feedback/Dialog.jsx":"161a08155458","components/feedback/LoadingSpinner.jsx":"92f275ac2f4e","components/feedback/Tooltip.jsx":"6e69b07b2e6d","components/forms/Checkbox.jsx":"8990506c2551","components/forms/Radio.jsx":"511ba812d43f","components/forms/Select.jsx":"20099ad55edb","components/forms/Switch.jsx":"3a75507a89f5","components/forms/TextInput.jsx":"f0f9a8d3d164","components/navigation/Breadcrumbs.jsx":"aea9c6759fd4","components/navigation/SideNavigation.jsx":"8a8376ed92f8","components/navigation/Tabs.jsx":"2818ad9fa5e5","ui_kits/aura_console/InstanceDetailScreen.jsx":"2c81fe0513b6","ui_kits/aura_console/InstancesScreen.jsx":"b7541b5e8a40","ui_kits/aura_console/QueryScreen.jsx":"01b3ec3b8f9f","ui_kits/aura_console/Shell.jsx":"6d232f0a9fe3","ui_kits/marketing/HomePage.jsx":"05338f2a2d9f","ui_kits/marketing/PricingPage.jsx":"d57bb6ab0b2c","ui_kits/marketing/SiteChrome.jsx":"d8a46f011eb7"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.Neo4jNeedleDesignSystem_eb581b = window.Neo4jNeedleDesignSystem_eb581b || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
function Badge({
  children,
  color = 'neutral',
  hasDot = false
}) {
  const map = {
    neutral: {
      fg: 'var(--text-weak)',
      bg: 'var(--canvas)',
      dot: 'var(--text-weakest)'
    },
    primary: {
      fg: 'var(--primary-text)',
      bg: 'var(--primary-bg)',
      dot: 'var(--primary-fill)'
    },
    success: {
      fg: 'var(--success-text)',
      bg: 'var(--success-bg)',
      dot: 'var(--success-text)'
    },
    warning: {
      fg: 'var(--warning-text)',
      bg: 'var(--warning-bg)',
      dot: 'var(--warning-text)'
    },
    danger: {
      fg: 'var(--danger-text)',
      bg: 'var(--danger-bg)',
      dot: 'var(--danger-text)'
    },
    discovery: {
      fg: 'var(--discovery-text)',
      bg: 'var(--discovery-bg)',
      dot: 'var(--discovery-text)'
    }
  };
  const c = map[color] || map.neutral;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      height: 24,
      padding: '0 8px',
      borderRadius: 'var(--radius-xs)',
      background: c.bg,
      color: c.fg,
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      fontSize: 12,
      lineHeight: 1,
      boxSizing: 'border-box'
    }
  }, hasDot && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: 9999,
      background: c.dot
    }
  }), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZES = {
  small: {
    height: 28,
    padding: '0 12px',
    fontSize: 12,
    gap: 6
  },
  medium: {
    height: 36,
    padding: '0 16px',
    fontSize: 14,
    gap: 8
  },
  large: {
    height: 44,
    padding: '0 20px',
    fontSize: 16,
    gap: 8
  }
};
function Button({
  children,
  fill = 'filled',
  color = 'primary',
  size = 'medium',
  isDisabled = false,
  isLoading = false,
  isFullWidth = false,
  htmlAttributes = {},
  onClick,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const s = SIZES[size] || SIZES.medium;
  const tokens = color === 'danger' ? {
    base: 'var(--danger-text)',
    hover: 'var(--danger-hover)',
    pressed: 'var(--danger-pressed)',
    tint: 'var(--danger-bg)'
  } : {
    base: 'var(--primary-fill)',
    hover: 'var(--primary-hover)',
    pressed: 'var(--primary-pressed)',
    tint: 'var(--primary-bg)'
  };
  const accent = press ? tokens.pressed : hover ? tokens.hover : tokens.base;
  let style = {
    display: isFullWidth ? 'flex' : 'inline-flex',
    width: isFullWidth ? '100%' : undefined,
    alignItems: 'center',
    justifyContent: 'center',
    gap: s.gap,
    height: s.height,
    padding: s.padding,
    boxSizing: 'border-box',
    fontFamily: 'var(--font-sans)',
    fontWeight: 700,
    fontSize: s.fontSize,
    lineHeight: 1,
    letterSpacing: '0.016rem',
    borderRadius: 'var(--radius-control)',
    border: '1px solid transparent',
    cursor: isDisabled ? 'not-allowed' : 'pointer',
    transition: 'background-color 140ms ease-out, color 140ms ease-out, border-color 140ms ease-out',
    whiteSpace: 'nowrap'
  };
  if (fill === 'filled') {
    style = {
      ...style,
      background: color === 'neutral' ? 'var(--text)' : accent,
      color: 'var(--text-inverse)'
    };
    if (color === 'neutral') style.color = 'var(--text-inverse)';
  } else if (fill === 'outlined') {
    style = {
      ...style,
      background: press ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent',
      color: color === 'neutral' ? 'var(--text)' : accent,
      borderColor: color === 'neutral' ? 'var(--border-strong)' : accent
    };
  } else {
    style = {
      ...style,
      background: press ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent',
      color: color === 'neutral' ? 'var(--text)' : accent
    };
  }

  // DERIVED — the source spec defines no disabled token; see tokens/theme-light.css.
  if (isDisabled) {
    style = {
      ...style,
      background: fill === 'filled' ? 'var(--disabled-fill)' : 'transparent',
      color: 'var(--disabled-text)',
      borderColor: fill === 'outlined' ? 'var(--disabled-border)' : 'transparent'
    };
  }
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    disabled: isDisabled || isLoading,
    style: style,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setPress(false);
    },
    onMouseDown: () => setPress(true),
    onMouseUp: () => setPress(false)
  }, htmlAttributes, rest), isLoading && /*#__PURE__*/React.createElement(Spinner, null), children);
}
function Spinner() {
  return /*#__PURE__*/React.createElement("svg", {
    width: "14",
    height: "14",
    viewBox: "0 0 16 16",
    fill: "none",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "8",
    cy: "8",
    r: "6.5",
    stroke: "currentColor",
    strokeWidth: "2",
    opacity: "0.3"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8 1.5A6.5 6.5 0 0 1 14.5 8",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("animateTransform", {
    attributeName: "transform",
    type: "rotate",
    from: "0 8 8",
    to: "360 8 8",
    dur: "0.7s",
    repeatCount: "indefinite"
  })));
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function Card({
  children,
  header,
  footer,
  padding = 'medium',
  isInteractive = false,
  onClick,
  style: styleProp
}) {
  const [hover, setHover] = React.useState(false);
  const pad = padding === 'none' ? 0 : padding === 'small' ? 16 : 24;
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      background: 'var(--surface)',
      border: '1px solid ' + (isInteractive && hover ? 'var(--border-strong)' : 'var(--border-weak)'),
      borderRadius: 'var(--radius-card)',
      boxShadow: 'var(--elevation-raised)',
      cursor: isInteractive ? 'pointer' : undefined,
      overflow: 'hidden',
      transition: 'border-color 140ms ease-out',
      ...styleProp
    }
  }, header && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: `${pad === 0 ? 16 : pad}px ${pad === 0 ? 16 : pad}px 0`
    }
  }, header), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: pad
    }
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: `0 ${pad === 0 ? 16 : pad}px ${pad === 0 ? 16 : pad}px`,
      borderTop: '1px solid var(--border-weak)',
      paddingTop: 16
    }
  }, footer));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZES = {
  small: 28,
  medium: 36,
  large: 44
};
function IconButton({
  children,
  ariaLabel,
  size = 'medium',
  fill = 'text',
  color = 'neutral',
  isDisabled = false,
  isActive = false,
  onClick,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const d = SIZES[size] || SIZES.medium;
  const accent = color === 'danger' ? 'var(--danger-text)' : color === 'primary' ? 'var(--primary-icon)' : 'var(--text-weak)';
  const bg = press || isActive ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent';
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    "aria-label": ariaLabel,
    disabled: isDisabled,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setPress(false);
    },
    onMouseDown: () => setPress(true),
    onMouseUp: () => setPress(false),
    style: {
      width: d,
      height: d,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 'var(--radius-control)',
      boxSizing: 'border-box',
      background: fill === 'outlined' ? bg === 'transparent' ? 'var(--surface)' : bg : bg,
      border: fill === 'outlined' ? '1px solid var(--border-strong)' : '1px solid transparent',
      color: isDisabled ? 'var(--disabled-text)' : accent,
      cursor: isDisabled ? 'not-allowed' : 'pointer',
      transition: 'background-color 140ms ease-out, color 140ms ease-out',
      padding: 0
    }
  }, rest), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function Tag({
  children,
  color = 'neutral',
  size = 'medium',
  onRemove
}) {
  const map = {
    neutral: {
      fg: 'var(--text-weak)',
      bg: 'var(--canvas)',
      bd: 'var(--border-weak)'
    },
    primary: {
      fg: 'var(--primary-text)',
      bg: 'var(--primary-bg)',
      bd: 'var(--primary-border-weak)'
    },
    success: {
      fg: 'var(--success-text)',
      bg: 'var(--success-bg)',
      bd: 'var(--success-border-weak)'
    },
    warning: {
      fg: 'var(--warning-text)',
      bg: 'var(--warning-bg)',
      bd: 'var(--warning-border-weak)'
    },
    danger: {
      fg: 'var(--danger-text)',
      bg: 'var(--danger-bg)',
      bd: 'var(--danger-border-weak)'
    },
    discovery: {
      fg: 'var(--discovery-text)',
      bg: 'var(--discovery-bg)',
      bd: 'var(--discovery-border-weak)'
    }
  };
  const c = map[color] || map.neutral;
  const s = size === 'small' ? {
    h: 20,
    fs: 12,
    px: 8
  } : {
    h: 24,
    fs: 12,
    px: 12
  };
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      height: s.h,
      padding: `0 ${s.px}px`,
      borderRadius: 'var(--radius-pill)',
      background: c.bg,
      color: c.fg,
      border: `1px solid ${c.bd}`,
      fontFamily: 'var(--font-sans)',
      fontWeight: 600,
      fontSize: s.fs,
      lineHeight: 1,
      whiteSpace: 'nowrap',
      boxSizing: 'border-box'
    }
  }, children, onRemove && /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": "Remove",
    onClick: onRemove,
    style: {
      background: 'none',
      border: 0,
      padding: 0,
      color: 'inherit',
      cursor: 'pointer',
      display: 'inline-flex',
      opacity: 0.7
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "12",
    height: "12",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  }))));
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/data/CodeBlock.jsx
try { (() => {
const KEYWORDS = /\b(MATCH|OPTIONAL MATCH|WHERE|RETURN|WITH|CREATE|MERGE|SET|DELETE|DETACH DELETE|ORDER BY|LIMIT|SKIP|UNWIND|CALL|YIELD|AS|AND|OR|NOT|IN|COUNT|DISTINCT)\b/g;
function CodeBlock({
  code = '',
  language = 'cypher',
  showLineNumbers = false,
  onCopy
}) {
  const lines = String(code).replace(/\n$/, '').split('\n');
  const highlight = line => {
    if (language !== 'cypher') return [line];
    const out = [];
    let last = 0;
    let m;
    KEYWORDS.lastIndex = 0;
    while (m = KEYWORDS.exec(line)) {
      if (m.index > last) out.push(line.slice(last, m.index));
      out.push(/*#__PURE__*/React.createElement("span", {
        key: m.index,
        style: {
          color: 'var(--discovery-text)',
          fontWeight: 500
        }
      }, m[0]));
      last = m.index + m[0].length;
    }
    out.push(line.slice(last));
    return out;
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      background: 'var(--canvas)',
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-m)',
      padding: '12px 16px',
      overflowX: 'auto'
    }
  }, /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      fontFamily: 'var(--font-code)',
      fontSize: 14,
      lineHeight: 1.43,
      color: 'var(--text)'
    }
  }, lines.map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      gap: 16
    }
  }, showLineNumbers && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-weakest)',
      userSelect: 'none',
      minWidth: 16,
      textAlign: 'right'
    }
  }, i + 1), /*#__PURE__*/React.createElement("span", null, highlight(l))))), onCopy && /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onCopy,
    style: {
      position: 'absolute',
      top: 8,
      right: 8,
      background: 'var(--surface)',
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-s)',
      padding: '4px 8px',
      cursor: 'pointer',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      fontSize: 12,
      color: 'var(--text-weak)'
    }
  }, "Copy"));
}
Object.assign(__ds_scope, { CodeBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/CodeBlock.jsx", error: String((e && e.message) || e) }); }

// components/data/DataTable.jsx
try { (() => {
function DataTable({
  columns = [],
  rows = [],
  isDense = false,
  emptyText = 'No results.',
  onRowClick
}) {
  const padY = isDense ? 6 : 12;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-card)',
      overflow: 'hidden',
      background: 'var(--surface)',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: isDense ? 12 : 14
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      background: 'var(--canvas)'
    }
  }, columns.map(c => /*#__PURE__*/React.createElement("th", {
    key: c.key,
    style: {
      textAlign: c.align || 'left',
      padding: `${padY}px 16px`,
      width: c.width,
      fontWeight: 700,
      fontSize: 12,
      lineHeight: 1.67,
      color: 'var(--text-weaker)',
      borderBottom: '1px solid var(--border-weak)',
      whiteSpace: 'nowrap'
    }
  }, c.header)))), /*#__PURE__*/React.createElement("tbody", null, rows.length === 0 && /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    colSpan: columns.length,
    style: {
      padding: 32,
      textAlign: 'center',
      color: 'var(--text-weaker)'
    }
  }, emptyText)), rows.map((r, i) => /*#__PURE__*/React.createElement(Row, {
    key: r.id ?? i,
    row: r,
    columns: columns,
    padY: padY,
    onClick: onRowClick
  })))));
}
function Row({
  row,
  columns,
  padY,
  onClick
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("tr", {
    onClick: () => onClick && onClick(row),
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      background: hover && onClick ? 'var(--neutral-hover)' : 'transparent',
      cursor: onClick ? 'pointer' : undefined,
      transition: 'background-color 140ms ease-out'
    }
  }, columns.map(c => /*#__PURE__*/React.createElement("td", {
    key: c.key,
    style: {
      padding: `${padY}px 16px`,
      textAlign: c.align || 'left',
      color: 'var(--text)',
      borderBottom: '1px solid var(--border-weak)',
      fontFamily: c.isCode ? 'var(--font-code)' : 'inherit',
      verticalAlign: 'middle'
    }
  }, c.render ? c.render(row) : row[c.key])));
}
Object.assign(__ds_scope, { DataTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/DataTable.jsx", error: String((e && e.message) || e) }); }

// components/data/GraphLegend.jsx
try { (() => {
const NODE_COLORS = ['#FFDF81', '#C990C0', '#F79767', '#56C7E4', '#F16767', '#D8C7AE', '#8DCC93', '#ECB4C9', '#4D8DDA', '#FFC354', '#DA7294', '#579380'];
function GraphLegend({
  labels = [],
  activeLabels,
  onToggle,
  title = 'Node labels'
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-sans)'
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 12,
      lineHeight: 1.67,
      color: 'var(--text-weaker)',
      marginBottom: 8
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6
    }
  }, labels.map((l, i) => {
    const name = typeof l === 'string' ? l : l.label;
    const count = typeof l === 'string' ? undefined : l.count;
    const color = typeof l === 'object' && l.color || NODE_COLORS[i % NODE_COLORS.length];
    const on = !activeLabels || activeLabels.includes(name);
    return /*#__PURE__*/React.createElement("button", {
      key: name,
      type: "button",
      onClick: () => onToggle && onToggle(name),
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        height: 24,
        padding: '0 10px',
        borderRadius: 'var(--radius-pill)',
        border: '1px solid var(--border-weak)',
        background: on ? color : 'var(--canvas)',
        color: on ? '#1A1B1D' : 'var(--text-weakest)',
        fontFamily: 'var(--font-sans)',
        fontWeight: 600,
        fontSize: 12,
        lineHeight: 1,
        cursor: onToggle ? 'pointer' : 'default',
        opacity: on ? 1 : 0.6,
        transition: 'background-color 140ms ease-out, opacity 140ms ease-out'
      }
    }, name, count != null && /*#__PURE__*/React.createElement("span", {
      style: {
        opacity: 0.7
      }
    }, count));
  })));
}
Object.assign(__ds_scope, { GraphLegend });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/GraphLegend.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Banner.jsx
try { (() => {
function Banner({
  title,
  children,
  type = 'info',
  icon,
  onDismiss,
  actions
}) {
  const map = {
    info: {
      fg: 'var(--primary-text)',
      bg: 'var(--primary-bg)',
      bd: 'var(--primary-border-weak)'
    },
    success: {
      fg: 'var(--success-text)',
      bg: 'var(--success-bg)',
      bd: 'var(--success-border-weak)'
    },
    warning: {
      fg: 'var(--warning-text)',
      bg: 'var(--warning-bg)',
      bd: 'var(--warning-border-weak)'
    },
    danger: {
      fg: 'var(--danger-text)',
      bg: 'var(--danger-bg)',
      bd: 'var(--danger-border-weak)'
    },
    discovery: {
      fg: 'var(--discovery-text)',
      bg: 'var(--discovery-bg)',
      bd: 'var(--discovery-border-weak)'
    }
  };
  const c = map[type] || map.info;
  return /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      display: 'flex',
      gap: 12,
      padding: 16,
      background: c.bg,
      border: `1px solid ${c.bd}`,
      borderRadius: 'var(--radius-card)',
      fontFamily: 'var(--font-sans)'
    }
  }, icon && /*#__PURE__*/React.createElement("span", {
    style: {
      color: c.fg,
      display: 'flex',
      flexShrink: 0,
      marginTop: 1
    }
  }, icon), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      lineHeight: 1.43,
      letterSpacing: '0.016rem',
      color: c.fg
    }
  }, title), children && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: 'var(--text-weak)',
      marginTop: title ? 4 : 0
    }
  }, children), actions && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 12
    }
  }, actions)), onDismiss && /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": "Dismiss",
    onClick: onDismiss,
    style: {
      background: 'none',
      border: 0,
      padding: 0,
      cursor: 'pointer',
      color: 'var(--text-weak)',
      display: 'flex',
      height: 20
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  }))));
}
Object.assign(__ds_scope, { Banner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Banner.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
function Dialog({
  isOpen = true,
  title,
  children,
  actions,
  onClose,
  size = 'medium'
}) {
  if (!isOpen) return null;
  const w = size === 'small' ? 400 : size === 'large' ? 720 : 560;
  return /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    onClick: onClose,
    style: {
      position: 'absolute',
      inset: 0,
      background: 'rgba(26,27,29,0.45)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
      zIndex: 40
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      width: w,
      maxWidth: '100%',
      background: 'var(--surface)',
      borderRadius: 'var(--radius-card-lg)',
      boxShadow: 'var(--elevation-overlay)',
      border: '1px solid var(--border-weak)',
      fontFamily: 'var(--font-sans)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 16,
      padding: '24px 24px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      fontWeight: 700,
      fontSize: 20,
      lineHeight: 1.4,
      letterSpacing: '0.016rem',
      color: 'var(--text)'
    }
  }, title), onClose && /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": "Close",
    onClick: onClose,
    style: {
      background: 'none',
      border: 0,
      padding: 4,
      margin: -4,
      cursor: 'pointer',
      color: 'var(--text-weak)',
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "20",
    height: "20",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 24px 24px',
      fontSize: 14,
      lineHeight: 1.43,
      color: 'var(--text-weak)'
    }
  }, children), actions && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'flex-end',
      gap: 8,
      padding: 16,
      borderTop: '1px solid var(--border-weak)',
      background: 'var(--canvas)'
    }
  }, actions)));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/LoadingSpinner.jsx
try { (() => {
function LoadingSpinner({
  size = 24,
  label
}) {
  return /*#__PURE__*/React.createElement("span", {
    role: "status",
    "aria-live": "polite",
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 16 16",
    fill: "none",
    "aria-hidden": "true",
    style: {
      color: 'var(--primary-icon)'
    }
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "8",
    cy: "8",
    r: "6.5",
    stroke: "currentColor",
    strokeWidth: "2",
    opacity: "0.25"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8 1.5A6.5 6.5 0 0 1 14.5 8",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("animateTransform", {
    attributeName: "transform",
    type: "rotate",
    from: "0 8 8",
    to: "360 8 8",
    dur: "0.7s",
    repeatCount: "indefinite"
  }))), label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: 'var(--text-weak)'
    }
  }, label));
}
Object.assign(__ds_scope, { LoadingSpinner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/LoadingSpinner.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function Tooltip({
  children,
  content,
  placement = 'top'
}) {
  const [open, setOpen] = React.useState(false);
  const pos = {
    top: {
      bottom: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      marginBottom: 6
    },
    bottom: {
      top: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      marginTop: 6
    },
    left: {
      right: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      marginRight: 6
    },
    right: {
      left: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      marginLeft: 6
    }
  }[placement];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      display: 'inline-flex'
    },
    onMouseEnter: () => setOpen(true),
    onMouseLeave: () => setOpen(false),
    onFocus: () => setOpen(true),
    onBlur: () => setOpen(false)
  }, children, open && /*#__PURE__*/React.createElement("span", {
    role: "tooltip",
    style: {
      position: 'absolute',
      ...pos,
      zIndex: 30,
      whiteSpace: 'nowrap',
      background: 'var(--text)',
      color: 'var(--text-inverse)',
      fontFamily: 'var(--font-sans)',
      fontSize: 12,
      lineHeight: 1.67,
      padding: '4px 8px',
      borderRadius: 'var(--radius-s)',
      boxShadow: 'var(--elevation-overlay)'
    }
  }, content));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function Checkbox({
  label,
  isChecked = false,
  isIndeterminate = false,
  onChange,
  isDisabled = false,
  helpText
}) {
  const on = isChecked || isIndeterminate;
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'inline-flex',
      gap: 8,
      alignItems: 'flex-start',
      cursor: isDisabled ? 'not-allowed' : 'pointer',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 18,
      height: 18,
      flex: '0 0 18px',
      marginTop: 1,
      borderRadius: 'var(--radius-xs)',
      boxSizing: 'border-box',
      background: isDisabled ? 'var(--disabled-fill)' : on ? 'var(--primary-fill)' : 'var(--surface)',
      border: `1px solid ${isDisabled ? 'var(--disabled-border)' : on ? 'var(--primary-fill)' : 'var(--border-strong)'}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background-color 140ms ease-out, border-color 140ms ease-out'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: isChecked,
    disabled: isDisabled,
    onChange: e => onChange && onChange(e.target.checked),
    style: {
      position: 'absolute',
      opacity: 0,
      width: 0,
      height: 0
    }
  }), isIndeterminate ? /*#__PURE__*/React.createElement("svg", {
    width: "10",
    height: "10",
    viewBox: "0 0 24 24",
    stroke: isDisabled ? 'var(--disabled-text)' : 'var(--text-inverse)',
    strokeWidth: "4",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 12h14"
  })) : isChecked && /*#__PURE__*/React.createElement("svg", {
    width: "12",
    height: "12",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: isDisabled ? 'var(--disabled-text)' : 'var(--text-inverse)',
    strokeWidth: "3.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M20 6 9 17l-5-5"
  }))), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)'
    }
  }, label), helpText && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 12,
      lineHeight: 1.67,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text-weaker)'
    }
  }, helpText)));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function Radio({
  label,
  value,
  name,
  isChecked = false,
  onChange,
  isDisabled = false,
  helpText
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'inline-flex',
      gap: 8,
      alignItems: 'flex-start',
      cursor: isDisabled ? 'not-allowed' : 'pointer',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 18,
      height: 18,
      flex: '0 0 18px',
      marginTop: 1,
      borderRadius: 9999,
      boxSizing: 'border-box',
      background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)',
      border: `${isChecked ? 5 : 1}px solid ${isDisabled ? 'var(--disabled-border)' : isChecked ? 'var(--primary-fill)' : 'var(--border-strong)'}`,
      transition: 'border 140ms ease-out'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "radio",
    name: name,
    value: value,
    checked: isChecked,
    disabled: isDisabled,
    onChange: () => onChange && onChange(value),
    style: {
      position: 'absolute',
      opacity: 0,
      width: 0,
      height: 0
    }
  })), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)'
    }
  }, label), helpText && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 12,
      lineHeight: 1.67,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text-weaker)'
    }
  }, helpText)));
}
Object.assign(__ds_scope, { Radio });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function Select({
  label,
  value,
  onChange,
  options = [],
  placeholder = 'Select…',
  helpText,
  errorText,
  isDisabled = false,
  size = 'medium',
  isFullWidth = false
}) {
  const [focus, setFocus] = React.useState(false);
  const h = size === 'small' ? 28 : size === 'large' ? 44 : 36;
  const invalid = Boolean(errorText);
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: isFullWidth ? 'flex' : 'inline-flex',
      flexDirection: 'column',
      gap: 4,
      width: isFullWidth ? '100%' : undefined,
      fontFamily: 'var(--font-sans)'
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      lineHeight: 1.43,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)'
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      display: 'block'
    }
  }, /*#__PURE__*/React.createElement("select", {
    value: value,
    disabled: isDisabled,
    onChange: e => onChange && onChange(e.target.value),
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: '100%',
      height: h,
      padding: '0 36px 0 12px',
      boxSizing: 'border-box',
      appearance: 'none',
      background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)',
      border: `1px solid ${isDisabled ? 'var(--disabled-border)' : invalid ? 'var(--danger-text)' : focus ? 'var(--primary-focus)' : 'var(--border-strong)'}`,
      outline: focus ? '2px solid var(--primary-focus)' : 'none',
      outlineOffset: 2,
      borderRadius: 'var(--radius-input)',
      fontFamily: 'var(--font-sans)',
      fontSize: size === 'small' ? 12 : 14,
      color: isDisabled ? 'var(--disabled-text)' : value ? 'var(--text)' : 'var(--text-weakest)',
      transition: 'border-color 140ms ease-out',
      cursor: isDisabled ? 'not-allowed' : 'pointer'
    }
  }, !value && /*#__PURE__*/React.createElement("option", {
    value: ""
  }, placeholder), options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label))), /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "var(--text-weak)",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    style: {
      position: 'absolute',
      right: 12,
      top: '50%',
      transform: 'translateY(-50%)',
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "m6 9 6 6 6-6"
  }))), (helpText || errorText) && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      lineHeight: 1.67,
      color: invalid ? 'var(--danger-text)' : 'var(--text-weaker)'
    }
  }, errorText || helpText));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function Switch({
  label,
  isChecked = false,
  onChange,
  isDisabled = false,
  size = 'medium'
}) {
  const w = size === 'small' ? 32 : 40,
    h = size === 'small' ? 18 : 22,
    k = h - 6;
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'inline-flex',
      gap: 8,
      alignItems: 'center',
      cursor: isDisabled ? 'not-allowed' : 'pointer',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: w,
      height: h,
      flex: `0 0 ${w}px`,
      borderRadius: 9999,
      boxSizing: 'border-box',
      position: 'relative',
      background: isDisabled ? 'var(--disabled-fill)' : isChecked ? 'var(--primary-fill)' : 'var(--border-strong)',
      transition: 'background-color 140ms ease-out'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: isChecked,
    disabled: isDisabled,
    onChange: e => onChange && onChange(e.target.checked),
    style: {
      position: 'absolute',
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 3,
      left: isChecked ? w - k - 3 : 3,
      width: k,
      height: k,
      borderRadius: 9999,
      background: isDisabled ? 'var(--disabled-text)' : 'var(--surface)',
      boxShadow: 'var(--elevation-raised)',
      transition: 'left 140ms ease-out'
    }
  })), label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)'
    }
  }, label));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextInput.jsx
try { (() => {
function TextInput({
  label,
  value,
  onChange,
  placeholder,
  helpText,
  errorText,
  isDisabled = false,
  isReadOnly = false,
  size = 'medium',
  leftIcon,
  rightIcon,
  type = 'text',
  isFullWidth = false
}) {
  const [focus, setFocus] = React.useState(false);
  const h = size === 'small' ? 28 : size === 'large' ? 44 : 36;
  const invalid = Boolean(errorText);
  const border = isDisabled ? 'var(--disabled-border)' : invalid ? 'var(--danger-text)' : focus ? 'var(--primary-focus)' : 'var(--border-strong)';
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: isFullWidth ? 'flex' : 'inline-flex',
      flexDirection: 'column',
      gap: 4,
      width: isFullWidth ? '100%' : undefined,
      fontFamily: 'var(--font-sans)'
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      lineHeight: 1.43,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)'
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      height: h,
      padding: '0 12px',
      boxSizing: 'border-box',
      background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)',
      border: `1px solid ${border}`,
      outline: focus ? '2px solid var(--primary-focus)' : 'none',
      outlineOffset: 2,
      borderRadius: 'var(--radius-input)',
      transition: 'border-color 140ms ease-out',
      color: 'var(--text-weak)'
    }
  }, leftIcon, /*#__PURE__*/React.createElement("input", {
    type: type,
    value: value,
    placeholder: placeholder,
    disabled: isDisabled,
    readOnly: isReadOnly,
    onChange: e => onChange && onChange(e.target.value),
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      flex: 1,
      minWidth: 0,
      border: 0,
      outline: 'none',
      background: 'transparent',
      fontFamily: 'var(--font-sans)',
      fontSize: size === 'small' ? 12 : 14,
      color: isDisabled ? 'var(--disabled-text)' : 'var(--text)',
      WebkitTextFillColor: isDisabled ? 'var(--disabled-text)' : undefined
    }
  }), rightIcon), (helpText || errorText) && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      lineHeight: 1.67,
      color: invalid ? 'var(--danger-text)' : 'var(--text-weaker)'
    }
  }, errorText || helpText));
}
Object.assign(__ds_scope, { TextInput });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextInput.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Breadcrumbs.jsx
try { (() => {
function Breadcrumbs({
  items = [],
  onNavigate
}) {
  return /*#__PURE__*/React.createElement("nav", {
    "aria-label": "Breadcrumb",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      lineHeight: 1.43,
      flexWrap: 'wrap'
    }
  }, items.map((it, i) => {
    const last = i === items.length - 1;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, last ? /*#__PURE__*/React.createElement("span", {
      "aria-current": "page",
      style: {
        color: 'var(--text)',
        fontWeight: 700
      }
    }, it.label) : /*#__PURE__*/React.createElement("a", {
      href: it.href || '#',
      onClick: e => {
        if (onNavigate) {
          e.preventDefault();
          onNavigate(it, i);
        }
      },
      style: {
        color: 'var(--text-weak)',
        textDecoration: 'none'
      }
    }, it.label), !last && /*#__PURE__*/React.createElement("svg", {
      width: "14",
      height: "14",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "var(--text-weakest)",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      "aria-hidden": "true"
    }, /*#__PURE__*/React.createElement("path", {
      d: "m9 18 6-6-6-6"
    })));
  }));
}
Object.assign(__ds_scope, { Breadcrumbs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Breadcrumbs.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SideNavigation.jsx
try { (() => {
function SideNavigation({
  items = [],
  value,
  onChange,
  header,
  footer,
  isCollapsed = false,
  width = 240
}) {
  return /*#__PURE__*/React.createElement("nav", {
    style: {
      width: isCollapsed ? 64 : width,
      flex: `0 0 ${isCollapsed ? 64 : width}px`,
      height: '100%',
      boxSizing: 'border-box',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border-weak)',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'var(--font-sans)',
      transition: 'width 160ms ease-out'
    }
  }, header && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: isCollapsed ? '16px 12px' : 16,
      borderBottom: '1px solid var(--border-weak)'
    }
  }, header), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: 'auto',
      padding: 8,
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    }
  }, items.map(it => it.isSection ? /*#__PURE__*/React.createElement("div", {
    key: it.label,
    style: {
      padding: isCollapsed ? '12px 0 4px' : '12px 12px 4px',
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--text-weakest)',
      letterSpacing: '0.016rem'
    }
  }, isCollapsed ? '' : it.label) : /*#__PURE__*/React.createElement(NavItem, {
    key: it.value,
    item: it,
    active: it.value === value,
    isCollapsed: isCollapsed,
    onClick: () => onChange && onChange(it.value)
  }))), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 12,
      borderTop: '1px solid var(--border-weak)'
    }
  }, footer));
}
function NavItem({
  item,
  active,
  isCollapsed,
  onClick
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClick,
    title: isCollapsed ? String(item.label) : undefined,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      width: '100%',
      boxSizing: 'border-box',
      padding: isCollapsed ? '8px 0' : '8px 12px',
      justifyContent: isCollapsed ? 'center' : 'flex-start',
      background: active ? 'var(--primary-bg)' : hover ? 'var(--neutral-hover)' : 'transparent',
      border: 0,
      borderRadius: 'var(--radius-control)',
      cursor: 'pointer',
      textAlign: 'left',
      color: active ? 'var(--primary-text)' : 'var(--text-weak)',
      fontFamily: 'var(--font-sans)',
      fontWeight: active ? 700 : 600,
      fontSize: 14,
      lineHeight: 1.43,
      transition: 'background-color 140ms ease-out, color 140ms ease-out'
    }
  }, item.icon && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      flexShrink: 0
    }
  }, item.icon), !isCollapsed && /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      minWidth: 0,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, item.label), !isCollapsed && item.trailing);
}
Object.assign(__ds_scope, { SideNavigation });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SideNavigation.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function Tabs({
  items = [],
  value,
  onChange,
  size = 'medium'
}) {
  const fs = size === 'small' ? 12 : 14;
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'flex',
      gap: 4,
      borderBottom: '1px solid var(--border-weak)',
      fontFamily: 'var(--font-sans)'
    }
  }, items.map(it => {
    const active = it.value === value;
    return /*#__PURE__*/React.createElement("button", {
      key: it.value,
      role: "tab",
      "aria-selected": active,
      type: "button",
      disabled: it.isDisabled,
      onClick: () => onChange && onChange(it.value),
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: size === 'small' ? '6px 12px' : '8px 16px',
        background: 'transparent',
        border: 0,
        borderBottom: `2px solid ${active ? 'var(--primary-border)' : 'transparent'}`,
        marginBottom: -1,
        cursor: it.isDisabled ? 'not-allowed' : 'pointer',
        opacity: it.isDisabled ? 0.45 : 1,
        fontFamily: 'var(--font-sans)',
        fontWeight: active ? 700 : 600,
        fontSize: fs,
        lineHeight: 1.43,
        color: active ? 'var(--primary-text)' : 'var(--text-weak)',
        transition: 'color 140ms ease-out, border-color 140ms ease-out'
      }
    }, it.icon, it.label, it.count != null && /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 700,
        color: 'var(--text-weaker)'
      }
    }, it.count));
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/aura_console/InstanceDetailScreen.jsx
try { (() => {
var {
  Button,
  Card,
  Badge,
  Tabs,
  Breadcrumbs,
  DataTable,
  CodeBlock,
  Switch,
  Banner
} = window.__NDL;
const CHART = [{
  day: 'Mon',
  a: 42,
  b: 18
}, {
  day: 'Tue',
  a: 61,
  b: 26
}, {
  day: 'Wed',
  a: 55,
  b: 22
}, {
  day: 'Thu',
  a: 78,
  b: 31
}, {
  day: 'Fri',
  a: 92,
  b: 40
}, {
  day: 'Sat',
  a: 34,
  b: 12
}, {
  day: 'Sun',
  a: 28,
  b: 10
}];
function BarChart() {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 12,
      height: 140
    }
  }, CHART.map(d => /*#__PURE__*/React.createElement("div", {
    key: d.day,
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 3,
      alignItems: 'flex-end',
      height: 120,
      width: '100%',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: '38%',
      height: d.a + '%',
      background: 'var(--chart-1)',
      borderRadius: '4px 4px 0 0'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: '38%',
      height: d.b + '%',
      background: 'var(--chart-2)',
      borderRadius: '4px 4px 0 0'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-weaker)'
    }
  }, d.day)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 16,
      marginTop: 12
    }
  }, [['Read queries', 'var(--chart-1)'], ['Write queries', 'var(--chart-2)']].map(([l, c]) => /*#__PURE__*/React.createElement("div", {
    key: l,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 12,
      color: 'var(--text-weak)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 10,
      borderRadius: 2,
      background: c
    }
  }), l))));
}
function InstanceDetailScreen({
  instance,
  onBack
}) {
  const [tab, setTab] = React.useState('overview');
  const [logging, setLogging] = React.useState(true);
  const [pauseNight, setPauseNight] = React.useState(false);
  const uri = 'neo4j+s://' + instance.name + '.databases.neo4j.io';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 32,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1100,
      margin: '0 auto'
    }
  }, /*#__PURE__*/React.createElement(Breadcrumbs, {
    onNavigate: onBack,
    items: [{
      label: 'Instances'
    }, {
      label: instance.name
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      margin: '12px 0 20px'
    }
  }, /*#__PURE__*/React.createElement("h1", {
    className: "ndl-title-1",
    style: {
      margin: 0,
      color: 'var(--text)'
    }
  }, instance.name), /*#__PURE__*/React.createElement(Badge, {
    color: instance.tone,
    hasDot: true
  }, instance.status), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(Button, {
    fill: "outlined",
    color: "neutral"
  }, "Pause instance"), /*#__PURE__*/React.createElement(Button, null, "Open in Query")), /*#__PURE__*/React.createElement(Tabs, {
    value: tab,
    onChange: setTab,
    items: [{
      value: 'overview',
      label: 'Overview'
    }, {
      value: 'connect',
      label: 'Connect'
    }, {
      value: 'metrics',
      label: 'Metrics'
    }, {
      value: 'settings',
      label: 'Settings'
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 24,
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, tab === 'overview' && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 16,
      alignItems: 'flex-start'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    style: {
      flex: 2
    },
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Query volume, last 7 days")
  }, /*#__PURE__*/React.createElement(BarChart, null)), /*#__PURE__*/React.createElement(Card, {
    style: {
      flex: 1
    },
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Details")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, [['Memory', instance.size], ['Compute', instance.cpu], ['Region', instance.region], ['Version', 'Neo4j ' + instance.version], ['Nodes', instance.nodes], ['Relationships', instance.rels]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "ndl-body-m",
    style: {
      color: 'var(--text-weak)'
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    className: "ndl-body-m",
    style: {
      color: 'var(--text)',
      fontWeight: 600
    }
  }, v)))))), tab === 'connect' && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Banner, {
    type: "info",
    title: "Credentials are shown once",
    icon: /*#__PURE__*/React.createElement(Ic, {
      d: ICONS.help,
      s: 18
    })
  }, "Download the credentials file when the instance is created. Neo4j does not store the password."), /*#__PURE__*/React.createElement(Card, {
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Connection URI")
  }, /*#__PURE__*/React.createElement(CodeBlock, {
    language: "plain",
    onCopy: () => {},
    code: uri
  })), /*#__PURE__*/React.createElement(Card, {
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Python driver")
  }, /*#__PURE__*/React.createElement(CodeBlock, {
    language: "plain",
    onCopy: () => {},
    showLineNumbers: true,
    code: 'from neo4j import GraphDatabase\n\ndriver = GraphDatabase.driver(\n    "' + uri + '",\n    auth=("neo4j", "<password>"))\n\nrecords, _, _ = driver.execute_query(\n    "MATCH (p:Person) RETURN p.name LIMIT 25")'
  }))), tab === 'metrics' && /*#__PURE__*/React.createElement(Card, {
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Slowest queries"),
    padding: "none"
  }, /*#__PURE__*/React.createElement(DataTable, {
    isDense: true,
    columns: [{
      key: 'q',
      header: 'Query',
      isCode: true
    }, {
      key: 'calls',
      header: 'Calls',
      align: 'right',
      isCode: true
    }, {
      key: 'p95',
      header: 'p95',
      align: 'right',
      isCode: true
    }],
    rows: [{
      q: 'MATCH (p:Person)-[:ORDERED*1..3]->(o:Order) RETURN o',
      calls: '4,102',
      p95: '812 ms'
    }, {
      q: 'MATCH (c:Company {name: $name}) RETURN c',
      calls: '88,410',
      p95: '14 ms'
    }, {
      q: 'MATCH (p:Product)<-[:CONTAINS]-(o:Order) RETURN p, count(o)',
      calls: '1,204',
      p95: '2,140 ms'
    }]
  })), tab === 'settings' && /*#__PURE__*/React.createElement(Card, {
    header: /*#__PURE__*/React.createElement("h2", {
      className: "ndl-title-4",
      style: {
        margin: 0
      }
    }, "Instance settings")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(Switch, {
    label: "Enable query logging",
    isChecked: logging,
    onChange: setLogging
  }), /*#__PURE__*/React.createElement(Switch, {
    label: "Pause instance overnight (22:00\u201306:00 UTC)",
    isChecked: pauseNight,
    onChange: setPauseNight
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--border-weak)',
      paddingTop: 16
    }
  }, /*#__PURE__*/React.createElement(Button, {
    color: "danger",
    fill: "outlined"
  }, "Delete instance")))))));
}
Object.assign(window, {
  InstanceDetailScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/aura_console/InstanceDetailScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/aura_console/InstancesScreen.jsx
try { (() => {
var {
  Button,
  Card,
  Badge,
  Tag,
  DataTable,
  TextInput,
  Select,
  Banner,
  Dialog,
  IconButton,
  Tooltip
} = window.__NDL;
const INSTANCES = [{
  id: 'orders-prod',
  name: 'orders-prod',
  status: 'Running',
  tone: 'success',
  size: '8 GB',
  cpu: '2 CPU',
  region: 'Europe (Ireland)',
  version: '5.26',
  nodes: '1,204,880',
  rels: '4,812,003'
}, {
  id: 'catalogue-prod',
  name: 'catalogue-prod',
  status: 'Running',
  tone: 'success',
  size: '4 GB',
  cpu: '1 CPU',
  region: 'Europe (Ireland)',
  version: '5.26',
  nodes: '388,140',
  rels: '901,556'
}, {
  id: 'analytics-dev',
  name: 'analytics-dev',
  status: 'Paused',
  tone: 'warning',
  size: '2 GB',
  cpu: '1 CPU',
  region: 'US East (N. Virginia)',
  version: '5.26',
  nodes: '92,004',
  rels: '188,220'
}, {
  id: 'fraud-sandbox',
  name: 'fraud-sandbox',
  status: 'Creating',
  tone: 'primary',
  size: '2 GB',
  cpu: '1 CPU',
  region: 'US East (N. Virginia)',
  version: '5.26',
  nodes: '—',
  rels: '—'
}];
function InstancesScreen({
  onOpenInstance
}) {
  const [query, setQuery] = React.useState('');
  const [region, setRegion] = React.useState('');
  const [confirm, setConfirm] = React.useState(null);
  const rows = INSTANCES.filter(i => i.name.includes(query) && (!region || i.region === region));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      minHeight: '100%',
      padding: 32,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1100,
      margin: '0 auto',
      display: 'flex',
      flexDirection: 'column',
      gap: 24
    }
  }, /*#__PURE__*/React.createElement(Banner, {
    type: "warning",
    title: "analytics-dev is paused",
    icon: /*#__PURE__*/React.createElement(Ic, {
      d: ICONS.pause,
      s: 18
    }),
    actions: /*#__PURE__*/React.createElement(Button, {
      size: "small",
      fill: "outlined",
      color: "neutral"
    }, "Resume instance")
  }, "Paused instances are not billed for compute but keep their storage. Data is retained for 30 days."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 16
    }
  }, [{
    label: 'Instances',
    value: '4',
    sub: '3 running'
  }, {
    label: 'Nodes',
    value: '1.68M',
    sub: 'across all instances'
  }, {
    label: 'Relationships',
    value: '5.90M',
    sub: 'across all instances'
  }, {
    label: 'Estimated spend',
    value: '$482',
    sub: 'month to date'
  }].map(s => /*#__PURE__*/React.createElement(Card, {
    key: s.label,
    padding: "small",
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--text-weaker)',
      lineHeight: 1.67
    }
  }, s.label), /*#__PURE__*/React.createElement("div", {
    className: "ndl-title-2",
    style: {
      color: 'var(--text)',
      marginTop: 4
    }
  }, s.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-weakest)',
      lineHeight: 1.67
    }
  }, s.sub)))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 12,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(TextInput, {
    placeholder: "Filter instances",
    value: query,
    onChange: setQuery,
    leftIcon: /*#__PURE__*/React.createElement(Ic, {
      d: ICONS.search,
      s: 16
    })
  }), /*#__PURE__*/React.createElement(Select, {
    value: region,
    onChange: setRegion,
    placeholder: "All regions",
    options: [{
      value: 'Europe (Ireland)',
      label: 'Europe (Ireland)'
    }, {
      value: 'US East (N. Virginia)',
      label: 'US East (N. Virginia)'
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(Button, {
    onClick: () => setConfirm('create')
  }, "Create instance")), /*#__PURE__*/React.createElement(DataTable, {
    onRowClick: r => onOpenInstance && onOpenInstance(r),
    columns: [{
      key: 'name',
      header: 'Name',
      render: r => /*#__PURE__*/React.createElement("div", {
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }
      }, /*#__PURE__*/React.createElement("span", {
        style: {
          fontWeight: 700,
          color: 'var(--text)'
        }
      }, r.name), /*#__PURE__*/React.createElement(Tag, {
        size: "small"
      }, r.version))
    }, {
      key: 'status',
      header: 'Status',
      render: r => /*#__PURE__*/React.createElement(Badge, {
        color: r.tone,
        hasDot: true
      }, r.status)
    }, {
      key: 'size',
      header: 'Size',
      render: r => r.size + ' · ' + r.cpu
    }, {
      key: 'region',
      header: 'Region'
    }, {
      key: 'nodes',
      header: 'Nodes',
      align: 'right',
      isCode: true
    }, {
      key: 'rels',
      header: 'Relationships',
      align: 'right',
      isCode: true
    }, {
      key: 'act',
      header: '',
      align: 'right',
      width: 88,
      render: r => /*#__PURE__*/React.createElement("div", {
        style: {
          display: 'flex',
          gap: 2,
          justifyContent: 'flex-end'
        },
        onClick: e => e.stopPropagation()
      }, /*#__PURE__*/React.createElement(Tooltip, {
        content: "Open in Query"
      }, /*#__PURE__*/React.createElement(IconButton, {
        size: "small",
        ariaLabel: "Open in Query"
      }, /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.terminal,
        s: 16
      }))), /*#__PURE__*/React.createElement(Tooltip, {
        content: "Delete instance"
      }, /*#__PURE__*/React.createElement(IconButton, {
        size: "small",
        color: "danger",
        ariaLabel: "Delete instance",
        onClick: () => setConfirm(r)
      }, /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.trash,
        s: 16
      }))))
    }],
    rows: rows,
    emptyText: "No instances match that filter."
  }))), /*#__PURE__*/React.createElement(Dialog, {
    isOpen: Boolean(confirm) && confirm !== 'create',
    size: "small",
    onClose: () => setConfirm(null),
    title: confirm && confirm !== 'create' ? 'Delete instance ' + confirm.name + '?' : '',
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      fill: "outlined",
      color: "neutral",
      onClick: () => setConfirm(null)
    }, "Cancel"), /*#__PURE__*/React.createElement(Button, {
      color: "danger",
      onClick: () => setConfirm(null)
    }, "Delete instance"))
  }, "This removes ", confirm && confirm !== 'create' ? confirm.nodes : '', " nodes and ", confirm && confirm !== 'create' ? confirm.rels : '', " relationships. It cannot be undone."), /*#__PURE__*/React.createElement(Dialog, {
    isOpen: confirm === 'create',
    onClose: () => setConfirm(null),
    title: "Create instance",
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      fill: "outlined",
      color: "neutral",
      onClick: () => setConfirm(null)
    }, "Cancel"), /*#__PURE__*/React.createElement(Button, {
      onClick: () => setConfirm(null)
    }, "Create instance"))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(TextInput, {
    isFullWidth: true,
    label: "Instance name",
    placeholder: "orders-staging",
    helpText: "Lowercase letters, numbers and hyphens."
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Select, {
    isFullWidth: true,
    label: "Region",
    value: "Europe (Ireland)",
    options: [{
      value: 'Europe (Ireland)',
      label: 'Europe (Ireland)'
    }, {
      value: 'US East (N. Virginia)',
      label: 'US East (N. Virginia)'
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Select, {
    isFullWidth: true,
    label: "Size",
    value: "4 GB",
    options: [{
      value: '2 GB',
      label: '2 GB memory · 1 CPU'
    }, {
      value: '4 GB',
      label: '4 GB memory · 1 CPU'
    }, {
      value: '8 GB',
      label: '8 GB memory · 2 CPU'
    }]
  }))))));
}
Object.assign(window, {
  InstancesScreen,
  INSTANCES
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/aura_console/InstancesScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/aura_console/QueryScreen.jsx
try { (() => {
var {
  Button,
  IconButton,
  Tooltip,
  Tabs,
  Tag,
  Badge,
  DataTable,
  CodeBlock,
  GraphLegend,
  LoadingSpinner,
  Banner
} = window.__NDL;
const NODE_COLORS = ['#FFDF81', '#C990C0', '#F79767', '#56C7E4', '#F16767', '#D8C7AE'];
const LABELS = [{
  label: 'Person',
  count: 412
}, {
  label: 'Company',
  count: 38
}, {
  label: 'Product',
  count: 1204
}, {
  label: 'Order',
  count: 8802
}];
const NODES = [{
  id: 1,
  x: 380,
  y: 210,
  r: 30,
  c: 0,
  t: 'Ada K.'
}, {
  id: 2,
  x: 540,
  y: 140,
  r: 26,
  c: 1,
  t: 'Neo4j'
}, {
  id: 3,
  x: 550,
  y: 310,
  r: 24,
  c: 2,
  t: 'Graph DB'
}, {
  id: 4,
  x: 260,
  y: 310,
  r: 22,
  c: 3,
  t: '#4021'
}, {
  id: 5,
  x: 280,
  y: 120,
  r: 22,
  c: 0,
  t: 'Tomas B.'
}, {
  id: 6,
  x: 700,
  y: 220,
  r: 20,
  c: 2,
  t: 'GDS'
}, {
  id: 7,
  x: 430,
  y: 400,
  r: 20,
  c: 3,
  t: '#4088'
}, {
  id: 8,
  x: 700,
  y: 380,
  r: 18,
  c: 4,
  t: 'Priya R.'
}, {
  id: 9,
  x: 200,
  y: 210,
  r: 18,
  c: 5,
  t: 'EU-W1'
}, {
  id: 10,
  x: 600,
  y: 70,
  r: 16,
  c: 1,
  t: 'Aura'
}];
const EDGES = [[1, 2], [1, 3], [1, 4], [5, 2], [3, 6], [4, 7], [7, 1], [8, 6], [9, 1], [2, 10], [5, 9], [8, 3]];
function GraphCanvas() {
  return /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: "100%",
    viewBox: "0 0 900 480",
    preserveAspectRatio: "xMidYMid slice",
    style: {
      display: 'block'
    }
  }, EDGES.map(([a, b], i) => {
    const n1 = NODES.find(n => n.id === a),
      n2 = NODES.find(n => n.id === b);
    return /*#__PURE__*/React.createElement("line", {
      key: i,
      x1: n1.x,
      y1: n1.y,
      x2: n2.x,
      y2: n2.y,
      stroke: "var(--border-strong)",
      strokeWidth: "1.5"
    });
  }), NODES.map(n => /*#__PURE__*/React.createElement("g", {
    key: n.id
  }, /*#__PURE__*/React.createElement("circle", {
    cx: n.x,
    cy: n.y,
    r: n.r,
    fill: NODE_COLORS[n.c],
    stroke: "var(--surface)",
    strokeWidth: "2"
  }), /*#__PURE__*/React.createElement("text", {
    x: n.x,
    y: n.y + 4,
    textAnchor: "middle",
    style: {
      font: '600 11px var(--font-sans)',
      fill: '#1A1B1D'
    }
  }, n.t))));
}
function Panel({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface)',
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-card-lg)',
      boxShadow: 'var(--elevation-overlay)',
      ...style
    }
  }, children);
}
function QueryScreen() {
  const [query, setQuery] = React.useState("MATCH (p:Person)-[:WORKS_AT]->(c:Company)\nWHERE c.name = 'Neo4j'\nRETURN p, c LIMIT 25");
  const [tab, setTab] = React.useState('graph');
  const [running, setRunning] = React.useState(false);
  const [active, setActive] = React.useState(LABELS.map(l => l.label));
  const [error, setError] = React.useState(false);
  const run = () => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      setError(query.indexOf('PURCHASED') > -1);
    }, 900);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: '100%',
      background: 'var(--canvas)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0
    }
  }, /*#__PURE__*/React.createElement(GraphCanvas, null)), /*#__PURE__*/React.createElement(Panel, {
    style: {
      position: 'absolute',
      top: 16,
      left: 16,
      right: 16,
      padding: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      alignItems: 'flex-start'
    }
  }, /*#__PURE__*/React.createElement("textarea", {
    value: query,
    onChange: e => setQuery(e.target.value),
    spellCheck: false,
    style: {
      flex: 1,
      minWidth: 0,
      height: 78,
      resize: 'none',
      boxSizing: 'border-box',
      fontFamily: 'var(--font-code)',
      fontSize: 14,
      lineHeight: 1.43,
      color: 'var(--text)',
      background: 'var(--canvas)',
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-m)',
      padding: '8px 12px',
      outlineColor: 'var(--primary-focus)',
      outlineOffset: 2
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Button, {
    onClick: run,
    isLoading: running
  }, running ? 'Running' : 'Run query'), /*#__PURE__*/React.createElement(Button, {
    fill: "text",
    size: "small"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.sparkle,
    s: 16
  }), " Cypher assist")))), /*#__PURE__*/React.createElement(Panel, {
    style: {
      position: 'absolute',
      top: 130,
      left: 16,
      width: 216,
      padding: 16
    }
  }, /*#__PURE__*/React.createElement(GraphLegend, {
    labels: LABELS,
    activeLabels: active,
    onToggle: l => setActive(a => a.indexOf(l) > -1 ? a.filter(x => x !== l) : a.concat(l))
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16,
      borderTop: '1px solid var(--border-weak)',
      paddingTop: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 12,
      color: 'var(--text-weaker)',
      marginBottom: 8
    }
  }, "Relationship types"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6
    }
  }, ['WORKS_AT', 'ORDERED', 'CONTAINS'].map(t => /*#__PURE__*/React.createElement(Tag, {
    key: t,
    size: "small"
  }, t))))), /*#__PURE__*/React.createElement(Panel, {
    style: {
      position: 'absolute',
      top: 130,
      right: 16,
      width: 300,
      padding: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 12,
      height: 12,
      borderRadius: 9999,
      background: '#FFDF81'
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "ndl-title-4",
    style: {
      color: 'var(--text)'
    }
  }, "Person"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(IconButton, {
    size: "small",
    ariaLabel: "Close inspector"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.close,
    s: 16
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, [['name', "'Ada Kensington'"], ['title', "'Staff engineer'"], ['joined', "date('2019-04-02')"], ['elementId', "'4:9f2a:118'"]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      gap: 12,
      fontSize: 12,
      lineHeight: 1.67
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-weaker)',
      fontFamily: 'var(--font-code)'
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text)',
      fontFamily: 'var(--font-code)',
      textAlign: 'right',
      wordBreak: 'break-all'
    }
  }, v))))), /*#__PURE__*/React.createElement(Panel, {
    style: {
      position: 'absolute',
      bottom: 216,
      right: 16,
      padding: 4,
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    }
  }, /*#__PURE__*/React.createElement(Tooltip, {
    content: "Zoom in",
    placement: "left"
  }, /*#__PURE__*/React.createElement(IconButton, {
    ariaLabel: "Zoom in"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.zoomIn
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    content: "Zoom out",
    placement: "left"
  }, /*#__PURE__*/React.createElement(IconButton, {
    ariaLabel: "Zoom out"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.zoomOut
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    content: "Fit to view",
    placement: "left"
  }, /*#__PURE__*/React.createElement(IconButton, {
    ariaLabel: "Fit to view"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.fit
  })))), /*#__PURE__*/React.createElement(Panel, {
    style: {
      position: 'absolute',
      bottom: 16,
      left: 16,
      right: 16,
      height: 188,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px'
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    size: "small",
    value: tab,
    onChange: setTab,
    items: [{
      value: 'graph',
      label: 'Graph'
    }, {
      value: 'table',
      label: 'Table',
      count: 25
    }, {
      value: 'plan',
      label: 'Query plan'
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 16,
      overflow: 'auto'
    }
  }, error && /*#__PURE__*/React.createElement(Banner, {
    type: "danger",
    title: "Query failed",
    icon: /*#__PURE__*/React.createElement(Ic, {
      d: ICONS.close,
      s: 18
    })
  }, "Unknown relationship type ", /*#__PURE__*/React.createElement("code", {
    className: "ndl-code"
  }, "PURCHASED_BY"), ". Run ", /*#__PURE__*/React.createElement("code", {
    className: "ndl-code"
  }, "CALL db.relationshipTypes()"), " to list valid types."), running && /*#__PURE__*/React.createElement(LoadingSpinner, {
    label: "Running query\u2026"
  }), !running && !error && tab === 'graph' && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      fontSize: 14,
      color: 'var(--text-weak)'
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    color: "success",
    hasDot: true
  }, "Completed"), /*#__PURE__*/React.createElement("span", null, "25 nodes, 24 relationships returned in ", /*#__PURE__*/React.createElement("span", {
    className: "ndl-code"
  }, "31 ms"), ".")), !running && !error && tab === 'table' && /*#__PURE__*/React.createElement(DataTable, {
    isDense: true,
    columns: [{
      key: 'p',
      header: 'p.name'
    }, {
      key: 'c',
      header: 'c.name'
    }, {
      key: 'id',
      header: 'elementId',
      isCode: true
    }],
    rows: [{
      p: 'Ada Kensington',
      c: 'Neo4j',
      id: '4:9f2a:118'
    }, {
      p: 'Tomas Bergh',
      c: 'Neo4j',
      id: '4:9f2a:204'
    }, {
      p: 'Priya Raman',
      c: 'Neo4j',
      id: '4:9f2a:377'
    }]
  }), !running && !error && tab === 'plan' && /*#__PURE__*/React.createElement(CodeBlock, {
    language: "plain",
    code: 'Operator          Estimated Rows   Rows\nProduceResults                25     25\nFilter                        25     25\nExpand(All)                  412    412\nNodeByLabelScan              412    412'
  }))));
}
Object.assign(window, {
  QueryScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/aura_console/QueryScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/aura_console/Shell.jsx
try { (() => {
var {
  SideNavigation,
  Badge,
  IconButton,
  Tooltip
} = window.__NDL;
function Ic({
  d,
  s = 20
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: s,
    height: s,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, d.map((p, i) => /*#__PURE__*/React.createElement("path", {
    key: i,
    d: p
  })));
}
const ICONS = {
  database: ['M3 5c0-1.7 4-3 9-3s9 1.3 9 3-4 3-9 3-9-1.3-9-3z', 'M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5', 'M3 12c0 1.7 4 3 9 3s9-1.3 9-3'],
  terminal: ['m4 17 6-6-6-6', 'M12 19h8'],
  upload: ['M12 3v12', 'm7 8 5-5 5 5', 'M3 17v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2'],
  sparkle: ['M12 3 13.9 8.6 19.5 10.5 13.9 12.4 12 18 10.1 12.4 4.5 10.5 10.1 8.6z'],
  users: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8', 'M22 21v-2a4 4 0 0 0-3-3.9'],
  settings: ['M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6', 'M19.6 13.4a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V4a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1z'],
  help: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20', 'M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3', 'M12 17h.01'],
  bell: ['M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9', 'M10.3 21a2 2 0 0 0 3.4 0'],
  plus: ['M12 5v14', 'M5 12h14'],
  search: ['m21 21-4.3-4.3', 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16'],
  play: ['m5 3 14 9-14 9V3z'],
  close: ['M18 6 6 18', 'M6 6l12 12'],
  copy: ['M8 4h10a2 2 0 0 1 2 2v10', 'M4 8h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2z'],
  zoomIn: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16', 'm21 21-4.3-4.3', 'M11 8v6', 'M8 11h6'],
  zoomOut: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16', 'm21 21-4.3-4.3', 'M8 11h6'],
  fit: ['M8 3H5a2 2 0 0 0-2 2v3', 'M16 3h3a2 2 0 0 1 2 2v3', 'M16 21h3a2 2 0 0 0 2-2v-3', 'M8 21H5a2 2 0 0 1-2-2v-3'],
  pause: ['M10 4H6v16h4z', 'M18 4h-4v16h4z'],
  trash: ['M3 6h18', 'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6', 'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2']
};
function TopBar({
  title,
  children
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      height: 56,
      flex: '0 0 56px',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '0 24px',
      background: 'var(--surface)',
      borderBottom: '1px solid var(--border-weak)',
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title), children, /*#__PURE__*/React.createElement(Tooltip, {
    content: "Notifications"
  }, /*#__PURE__*/React.createElement(IconButton, {
    ariaLabel: "Notifications"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.bell
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    content: "Help"
  }, /*#__PURE__*/React.createElement(IconButton, {
    ariaLabel: "Help"
  }, /*#__PURE__*/React.createElement(Ic, {
    d: ICONS.help
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 9999,
      background: 'var(--primary-fill)',
      color: 'var(--text-inverse)',
      display: 'grid',
      placeItems: 'center',
      fontWeight: 700,
      fontSize: 12,
      marginLeft: 4
    }
  }, "AK"));
}
function AppShell({
  page,
  onNavigate,
  title,
  topBarActions,
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      height: '100%',
      background: 'var(--canvas)',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement(SideNavigation, {
    value: page,
    onChange: onNavigate,
    width: 228,
    header: /*#__PURE__*/React.createElement("img", {
      src: "../../assets/logo-lockup-horizontal.svg",
      alt: "Neo4j Graph Intelligence Platform",
      style: {
        width: 148,
        display: 'block'
      }
    }),
    items: [{
      value: 'instances',
      label: 'Instances',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.database
      })
    }, {
      value: 'query',
      label: 'Query',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.terminal
      })
    }, {
      value: 'import',
      label: 'Import',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.upload
      })
    }, {
      value: 'assist',
      label: 'Cypher assist',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.sparkle
      }),
      trailing: /*#__PURE__*/React.createElement(Badge, {
        color: "discovery"
      }, "New")
    }, {
      isSection: true,
      label: 'Organisation'
    }, {
      value: 'members',
      label: 'Members',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.users
      })
    }, {
      value: 'settings',
      label: 'Settings',
      icon: /*#__PURE__*/React.createElement(Ic, {
        d: ICONS.settings
      })
    }],
    footer: /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        lineHeight: 1.67,
        color: 'var(--text-weaker)'
      }
    }, "Kensington Retail", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
      style: {
        color: 'var(--text-weakest)'
      }
    }, "Professional plan"))
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement(TopBar, {
    title: title
  }, topBarActions), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minHeight: 0,
      overflow: 'auto'
    }
  }, children)));
}
Object.assign(window, {
  Ic,
  ICONS,
  TopBar,
  AppShell
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/aura_console/Shell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing/HomePage.jsx
try { (() => {
var {
  Button,
  Tag,
  CodeBlock,
  Card
} = window.__NDL;
function Hero() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--gradient-baltic)',
      color: '#FCF9F6'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '96px 32px',
      display: 'flex',
      gap: 64,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: '4px 12px',
      borderRadius: 9999,
      border: '1px solid rgba(252,249,246,0.3)',
      fontSize: 12,
      fontWeight: 600,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: 9999,
      background: 'var(--brand-highlight-yellow)'
    }
  }), "Aura 5.26 is generally available"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 56,
      lineHeight: 1.2,
      margin: 0,
      fontFeatureSettings: '"lnum" 1, "pnum" 1',
      letterSpacing: '-0.01em'
    }
  }, "Ask harder questions", /*#__PURE__*/React.createElement("br", null), "of your data"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 20,
      lineHeight: 1.5,
      color: '#E7FAFB',
      marginTop: 24,
      maxWidth: 520
    }
  }, "Store data as nodes and relationships, then traverse them in milliseconds. Neo4j is the graph database behind fraud detection, supply chains, recommendations and knowledge graphs."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      marginTop: 32
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      height: 48,
      padding: '0 24px',
      borderRadius: 'var(--radius-control)',
      border: 0,
      cursor: 'pointer',
      background: '#FCF9F6',
      color: '#014063',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      fontSize: 16,
      letterSpacing: '0.016rem'
    }
  }, "Start free"), /*#__PURE__*/React.createElement("button", {
    style: {
      height: 48,
      padding: '0 24px',
      borderRadius: 'var(--radius-control)',
      cursor: 'pointer',
      background: 'transparent',
      color: '#FCF9F6',
      border: '1px solid rgba(252,249,246,0.5)',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      fontSize: 16,
      letterSpacing: '0.016rem'
    }
  }, "Talk to sales")), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 3,
      width: 88,
      background: 'var(--brand-periwinkle)',
      borderRadius: 9999,
      marginTop: 48
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      maxWidth: 480
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#FCF9F6',
      borderRadius: 'var(--radius-xl)',
      padding: 24,
      boxShadow: 'var(--elevation-overlay)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--text-weaker)',
      marginBottom: 12
    }
  }, "Find fraud rings three hops out"), /*#__PURE__*/React.createElement(CodeBlock, {
    code: "MATCH (a:Account)-[:TRANSFERRED*1..3]->(b:Account)\nWHERE a.flagged = true\nRETURN b.id, count(*) AS hops\nORDER BY hops DESC LIMIT 10"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      marginTop: 16,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(Tag, {
    size: "small",
    color: "primary"
  }, "Cypher"), /*#__PURE__*/React.createElement(Tag, {
    size: "small"
  }, "31 ms"), /*#__PURE__*/React.createElement(Tag, {
    size: "small"
  }, "4.8M relationships"))))));
}
function LogoBand() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--brand-off-white)',
      borderBottom: '1px solid var(--border-weak)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '32px',
      display: 'flex',
      alignItems: 'center',
      gap: 48
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--text-weaker)',
      whiteSpace: 'nowrap'
    }
  }, "Trusted in production by"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 40,
      flex: 1,
      justifyContent: 'space-between',
      opacity: 0.55
    }
  }, ['Customer logo', 'Customer logo', 'Customer logo', 'Customer logo', 'Customer logo'].map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      height: 32,
      borderRadius: 'var(--radius-s)',
      border: '1px dashed var(--border-strong)',
      display: 'grid',
      placeItems: 'center',
      fontSize: 11,
      color: 'var(--text-weakest)'
    }
  }, l)))));
}
function Features() {
  const items = [{
    t: 'Native graph storage',
    d: 'Relationships are stored as first-class records, so a traversal is a pointer hop, not a join. Query time stays flat as the graph grows.',
    c: 'var(--brand-forest)'
  }, {
    t: 'Cypher, the graph language',
    d: 'Draw the pattern you are looking for and the database finds it. Cypher is the basis of the ISO GQL standard.',
    c: 'var(--brand-baltic-dark)'
  }, {
    t: 'Graph data science',
    d: 'Sixty-five algorithms — centrality, community detection, similarity, embeddings — run in-database on the whole graph.',
    c: 'var(--brand-marigold)'
  }];
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--brand-off-white)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '96px 32px'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 40,
      lineHeight: 1.2,
      margin: 0,
      color: 'var(--brand-black)',
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, "Connections change everything"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 20,
      lineHeight: 1.5,
      color: 'var(--text-weak)',
      marginTop: 16,
      maxWidth: 620
    }
  }, "Relational databases store rows and reconstruct relationships at query time. A graph database stores the relationships."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 24,
      marginTop: 48
    }
  }, items.map(i => /*#__PURE__*/React.createElement("div", {
    key: i.t,
    style: {
      background: 'var(--surface)',
      border: '1px solid var(--border-weak)',
      borderRadius: 'var(--radius-xl)',
      padding: 32,
      boxShadow: 'var(--elevation-raised)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 40,
      height: 4,
      background: i.c,
      borderRadius: 9999
    }
  }), /*#__PURE__*/React.createElement("h3", {
    className: "ndl-title-3",
    style: {
      color: 'var(--text)',
      marginTop: 20,
      marginBottom: 8
    }
  }, i.t), /*#__PURE__*/React.createElement("p", {
    className: "ndl-body-l",
    style: {
      color: 'var(--text-weak)',
      margin: 0
    }
  }, i.d))))));
}
function Quote() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--brand-cream)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 860,
      margin: '0 auto',
      padding: '96px 32px',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("blockquote", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 32,
      lineHeight: 1.3,
      margin: 0,
      color: 'var(--brand-black)',
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, "\u201CWe moved a query that took eleven minutes in Postgres down to under a second. The model matched the problem, so the query stopped fighting it.\u201D"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 24,
      fontSize: 14,
      fontWeight: 700,
      color: 'var(--text)'
    }
  }, "Placeholder attribution"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: 'var(--text-weak)'
    }
  }, "No customer quotes were supplied \u2014 replace before publishing.")));
}
function Stats() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--gradient-forest)',
      color: '#FCF9F6'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '64px 32px',
      display: 'flex',
      gap: 48
    }
  }, [['84,000+', 'Community members'], ['800+', 'Enterprise customers'], ['65', 'Graph algorithms'], ['ISO GQL', 'Standard query language']].map(([v, l]) => /*#__PURE__*/React.createElement("div", {
    key: l,
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 40,
      lineHeight: 1.2,
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, v), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: 'rgba(252,249,246,0.85)',
      marginTop: 4
    }
  }, l)))));
}
function CTA() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      background: 'var(--brand-off-white)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '96px 32px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--brand-baltic-darkest)',
      borderRadius: 'var(--radius-2xl)',
      padding: 64,
      display: 'flex',
      alignItems: 'center',
      gap: 48
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 40,
      lineHeight: 1.2,
      margin: 0,
      color: '#FCF9F6',
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, "Start with a free instance"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 16,
      lineHeight: 1.5,
      color: '#CFD1D4',
      marginTop: 12,
      maxWidth: 480
    }
  }, "200,000 nodes and 400,000 relationships, no card required. Load a sample dataset and run your first traversal in under five minutes.")), /*#__PURE__*/React.createElement("button", {
    style: {
      height: 48,
      padding: '0 24px',
      borderRadius: 'var(--radius-control)',
      border: 0,
      cursor: 'pointer',
      background: '#FCF9F6',
      color: '#014063',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      fontSize: 16,
      letterSpacing: '0.016rem',
      whiteSpace: 'nowrap'
    }
  }, "Start free"))));
}
function HomePage() {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Hero, null), /*#__PURE__*/React.createElement(LogoBand, null), /*#__PURE__*/React.createElement(Features, null), /*#__PURE__*/React.createElement(Quote, null), /*#__PURE__*/React.createElement(Stats, null), /*#__PURE__*/React.createElement(CTA, null));
}
Object.assign(window, {
  HomePage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing/HomePage.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing/PricingPage.jsx
try { (() => {
var {
  Button,
  Card,
  Badge,
  Tag
} = window.__NDL;
const PLANS = [{
  name: 'AuraDB Free',
  price: '$0',
  unit: 'forever',
  blurb: 'For learning, prototypes and small side projects.',
  features: ['200k nodes, 400k relationships', '1 instance', 'Pauses after 3 days idle', 'Community support'],
  cta: 'Start free',
  featured: false
}, {
  name: 'AuraDB Professional',
  price: '$65',
  unit: 'per GB / month',
  blurb: 'For production applications that need to stay up.',
  features: ['1 GB to 128 GB memory', 'Unlimited instances', 'Daily backups, 7-day retention', 'Email support'],
  cta: 'Start free trial',
  featured: true
}, {
  name: 'AuraDB Business Critical',
  price: 'Custom',
  unit: 'annual contract',
  blurb: 'For regulated and high-availability workloads.',
  features: ['Multi-region availability', 'VPC peering and private link', 'Point-in-time recovery', '24/7 support with SLA'],
  cta: 'Talk to sales',
  featured: false
}];
function Check() {
  return /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "var(--success-text)",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    style: {
      flexShrink: 0,
      marginTop: 3
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M20 6 9 17l-5-5"
  }));
}
function PricingPage() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--brand-off-white)'
    }
  }, /*#__PURE__*/React.createElement("section", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '80px 32px 0',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 48,
      lineHeight: 1.2,
      margin: 0,
      color: 'var(--brand-black)',
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, "Pay for what you run"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 20,
      lineHeight: 1.5,
      color: 'var(--text-weak)',
      marginTop: 16,
      maxWidth: 560,
      marginLeft: 'auto',
      marginRight: 'auto'
    }
  }, "Instances are billed per GB of memory per hour. Pause an instance and you keep the storage without the compute cost.")), /*#__PURE__*/React.createElement("section", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '48px 32px 96px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 24,
      alignItems: 'stretch'
    }
  }, PLANS.map(p => /*#__PURE__*/React.createElement("div", {
    key: p.name,
    style: {
      background: 'var(--surface)',
      borderRadius: 'var(--radius-xl)',
      padding: 32,
      border: '1px solid ' + (p.featured ? 'var(--primary-border)' : 'var(--border-weak)'),
      boxShadow: p.featured ? 'var(--elevation-overlay)' : 'var(--elevation-raised)',
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("h2", {
    className: "ndl-title-3",
    style: {
      margin: 0,
      color: 'var(--text)'
    }
  }, p.name), p.featured && /*#__PURE__*/React.createElement(Badge, {
    color: "primary"
  }, "Most popular")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 40,
      lineHeight: 1.2,
      color: 'var(--text)',
      fontFeatureSettings: '"lnum" 1, "pnum" 1'
    }
  }, p.price), /*#__PURE__*/React.createElement("span", {
    className: "ndl-body-m",
    style: {
      color: 'var(--text-weaker)'
    }
  }, p.unit)), /*#__PURE__*/React.createElement("p", {
    className: "ndl-body-m",
    style: {
      color: 'var(--text-weak)',
      margin: 0
    }
  }, p.blurb), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      flex: 1
    }
  }, p.features.map(ft => /*#__PURE__*/React.createElement("div", {
    key: ft,
    style: {
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Check, null), /*#__PURE__*/React.createElement("span", {
    className: "ndl-body-m",
    style: {
      color: 'var(--text)'
    }
  }, ft)))), /*#__PURE__*/React.createElement(Button, {
    isFullWidth: true,
    size: "large",
    fill: p.featured ? 'filled' : 'outlined',
    color: p.featured ? 'primary' : 'neutral'
  }, p.cta)))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 48,
      background: 'var(--brand-cream)',
      borderRadius: 'var(--radius-xl)',
      padding: 32,
      display: 'flex',
      gap: 32,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("h3", {
    className: "ndl-title-3",
    style: {
      margin: 0,
      color: 'var(--brand-black)'
    }
  }, "Self-managed instead?"), /*#__PURE__*/React.createElement("p", {
    className: "ndl-body-l",
    style: {
      color: 'var(--text-weak)',
      margin: '8px 0 0'
    }
  }, "Neo4j Community Edition is free and open source under GPLv3. Enterprise Edition adds clustering, role-based access control and hot backups.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Button, {
    fill: "outlined",
    color: "neutral"
  }, "Download"), /*#__PURE__*/React.createElement(Button, null, "Compare editions")))));
}
Object.assign(window, {
  PricingPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing/PricingPage.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing/SiteChrome.jsx
try { (() => {
var {
  Button
} = window.__NDL;
function SiteHeader({
  onNav,
  page
}) {
  const links = ['Product', 'Solutions', 'Developers', 'Pricing', 'Company'];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 20,
      background: 'var(--brand-off-white)',
      borderBottom: '1px solid var(--border-weak)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '0 32px',
      height: 72,
      display: 'flex',
      alignItems: 'center',
      gap: 32
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => {
      e.preventDefault();
      onNav('home');
    },
    style: {
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-lockup-horizontal.svg",
    alt: "Neo4j Graph Intelligence Platform",
    style: {
      width: 168,
      display: 'block'
    }
  })), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      gap: 4,
      flex: 1
    }
  }, links.map(l => {
    const key = l.toLowerCase();
    const active = page === key;
    return /*#__PURE__*/React.createElement("a", {
      key: l,
      href: "#",
      onClick: e => {
        e.preventDefault();
        onNav(key);
      },
      style: {
        padding: '8px 12px',
        borderRadius: 'var(--radius-control)',
        textDecoration: 'none',
        fontWeight: active ? 700 : 600,
        fontSize: 14,
        color: active ? 'var(--primary-text)' : 'var(--text-weak)',
        background: active ? 'var(--primary-bg)' : 'transparent'
      }
    }, l);
  })), /*#__PURE__*/React.createElement(Button, {
    fill: "text",
    size: "small"
  }, "Sign in"), /*#__PURE__*/React.createElement(Button, {
    size: "medium"
  }, "Start free")));
}
function SiteFooter() {
  const cols = [['Product', ['Aura', 'Graph Data Science', 'Cypher', 'Bloom', 'Connectors']], ['Developers', ['Documentation', 'Developer guides', 'Community forum', 'GraphAcademy', 'Drivers']], ['Company', ['About', 'Customers', 'Careers', 'Newsroom', 'Contact']]];
  return /*#__PURE__*/React.createElement("footer", {
    style: {
      background: 'var(--brand-black)',
      color: '#FCF9F6'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '64px 32px 32px',
      display: 'flex',
      gap: 64
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 260
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-lockup-stacked-white.svg",
    alt: "Neo4j",
    style: {
      width: 160,
      display: 'block'
    }
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      lineHeight: 1.43,
      color: '#A8ACB2',
      marginTop: 20
    }
  }, "The graph database and knowledge graph platform for connected data.")), cols.map(([title, items]) => /*#__PURE__*/React.createElement("div", {
    key: title,
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      letterSpacing: '0.016rem',
      marginBottom: 12
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, items.map(i => /*#__PURE__*/React.createElement("a", {
    key: i,
    href: "#",
    onClick: e => e.preventDefault(),
    style: {
      fontSize: 14,
      color: '#CFD1D4',
      textDecoration: 'none'
    }
  }, i)))))), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: '0 auto',
      padding: '24px 32px 48px',
      borderTop: '1px solid #3C3F44',
      display: 'flex',
      gap: 24,
      fontSize: 12,
      color: '#818790'
    }
  }, /*#__PURE__*/React.createElement("span", null, "\xA9 2026 Neo4j, Inc."), /*#__PURE__*/React.createElement("span", null, "Privacy"), /*#__PURE__*/React.createElement("span", null, "Terms"), /*#__PURE__*/React.createElement("span", null, "Trust centre")));
}
Object.assign(window, {
  SiteHeader,
  SiteFooter
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing/SiteChrome.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.CodeBlock = __ds_scope.CodeBlock;

__ds_ns.DataTable = __ds_scope.DataTable;

__ds_ns.GraphLegend = __ds_scope.GraphLegend;

__ds_ns.Banner = __ds_scope.Banner;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.LoadingSpinner = __ds_scope.LoadingSpinner;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.TextInput = __ds_scope.TextInput;

__ds_ns.Breadcrumbs = __ds_scope.Breadcrumbs;

__ds_ns.SideNavigation = __ds_scope.SideNavigation;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
