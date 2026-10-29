/* The Heat Tax: charts and the race-day forecast tool.
   Data: window.HEAT_DATA from assets/heat_data.js (written by export_web.py).
   Network: the forecast tool calls Open-Meteo only (api., archive-api. and
   geocoding-api.open-meteo.com). Nothing else is requested and nothing is stored. */
(function () {
  "use strict";
  var D = window.HEAT_DATA;
  if (!D) return;
  var NS = "http://www.w3.org/2000/svg";
  var KNOT = D.model.knot;
  var YR = {};
  D.years.forEach(function (r) { YR[r.y] = r; });

  function el(tag, at, parent, txt) {
    var e = document.createElementNS(NS, tag);
    for (var k in at) e.setAttribute(k, at[k]);
    if (txt != null) e.textContent = txt;
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, at, parent, txt) {
    var e = document.createElement(tag);
    for (var k in at) e.setAttribute(k, at[k]);
    if (txt != null) e.textContent = txt;
    if (parent) parent.appendChild(e);
    return e;
  }
  function hm(m) { var s = Math.round(m * 60), hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60); return hh + ":" + (mm < 10 ? "0" : "") + mm; }
  function hms(m) { var s = Math.round(m * 60), hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60), ss = s % 60; return hh + ":" + (mm < 10 ? "0" : "") + mm + ":" + (ss < 10 ? "0" : "") + ss; }
  function sgn(v, d) { var r = +Math.abs(v).toFixed(d); return (r === 0 ? "" : v > 0 ? "+" : "\u2212") + r.toFixed(d); }
  function width(box) { return Math.max(300, box.clientWidth - 20); }
  function onResize(fn) { var t; window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(fn, 120); }); }
  function seg(group, fn) {
    if (!group) return;
    var bs = group.querySelectorAll("button");
    bs.forEach(function (b) {
      b.addEventListener("click", function () {
        bs.forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
        fn(b.getAttribute("data-k"));
      });
    });
  }
  function slopeOf(key) { for (var i = 0; i < D.slopes.length; i++) if (D.slopes[i].series === key) return D.slopes[i]; }
  var ERA_CLS = ["e0", "e1", "e2"];

  // markers: era 0 hollow circle, era 1 square, era 2 filled circle (shape carries era too)
  function marker(s, era, x, y, r, extra) {
    var m;
    if (era === 1) m = el("rect", { x: x - r * 0.9, y: y - r * 0.9, width: r * 1.8, height: r * 1.8 }, s);
    else m = el("circle", { cx: x, cy: y, r: r }, s);
    m.setAttribute("class", "mk " + ERA_CLS[era] + (extra ? " " + extra : ""));
    return m;
  }

  // ------------------------------------------------------------ 80-year scatter
  (function () {
    var box = document.getElementById("era-chart");
    if (!box) return;
    var read = document.getElementById("era-read"), title = document.getElementById("era-title");
    var K = box.getAttribute("data-series") || "men_25th";
    var LAB = { 1976: 1, 2012: 1, 2004: 1, 2018: 1, 2011: 1, 1994: 1, 1943: 0, 2017: 1 };
    function draw() {
      var S = D.series[K], sl = slopeOf(K), front = S.tier === "front";
      var W = width(box), H = W < 560 ? 320 : 400, L = 46, R = 14, T = 16, B = 42;
      var rows = S.rows.map(function (r) { var y = YR[r[0]]; return { y: r[0], t: front ? y.te : y.tf, d: r[3], era: y.era, ho: y.ho, v: r[1], tr: r[2] }; });
      var dmin = Math.min.apply(null, rows.map(function (r) { return r.d; })), dmax = Math.max.apply(null, rows.map(function (r) { return r.d; }));
      var step = (dmax - dmin) > 24 ? 10 : 5;
      var y0 = Math.floor((dmin - 2) / step) * step, y1 = Math.ceil((dmax + 2) / step) * step;
      var X = function (v) { return L + (v - 35) / (92 - 35) * (W - L - R); };
      var Y = function (v) { return T + (y1 - v) / (y1 - y0) * (H - T - B); };
      box.innerHTML = "";
      var s = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "img",
        "aria-label": "Scatter of race-day temperature against " + S.label.toLowerCase() + " time relative to its long-run trend, one point per race, " + rows.length + " races, with the fitted line flat to " + KNOT + " degrees and rising after." }, box);
      for (var v = y0; v <= y1; v += step) {
        el("line", { class: "grid" + (v === 0 ? " zero" : ""), x1: L, x2: W - R, y1: Y(v), y2: Y(v) }, s);
        el("text", { x: L - 6, y: Y(v) + 4, "text-anchor": "end" }, s, (v > 0 ? "+" : "") + v + "%");
      }
      for (var t = 40; t <= 90; t += 10) el("text", { x: X(t), y: H - B + 18, "text-anchor": "middle" }, s, t + "°F");
      el("text", { x: W - R, y: H - 6, "text-anchor": "end" }, s, "race-day temperature on the course");
      el("text", { x: L + 4, y: T + 2 }, s, "slower than trend ↑");
      var b = sl.beta_pct;
      el("polyline", { class: "fit", points: X(36) + "," + Y(0) + " " + X(KNOT) + "," + Y(0) + " " + X(90) + "," + Y(b * (90 - KNOT)) }, s);
      rows.sort(function (a, c) { return a.era - c.era; });
      var marks = [];
      rows.forEach(function (r) {
        var m = marker(s, r.era, X(r.t), Y(r.d), W < 560 ? 5 : 6, r.ho ? "ho" : "");
        m.setAttribute("tabindex", "0");
        m.setAttribute("aria-label", r.y + ", " + r.t.toFixed(1) + " degrees, " + sgn(r.d, 1) + " percent against trend" + (r.ho ? ", holdout year" : ""));
        var show = function () {
          marks.forEach(function (q) { q.classList.remove("sel"); }); m.classList.add("sel");
          read.textContent = r.y + (r.ho ? " (holdout)" : "") + "  ·  " + r.t.toFixed(1) + "°F  ·  " + S.label.toLowerCase() + " " + hms(r.v) + "  ·  " + sgn(r.d, 1) + "% against the trend (" + hm(r.tr) + ")";
        };
        m.addEventListener("mouseenter", show); m.addEventListener("focus", show); m.addEventListener("click", show);
        marks.push(m);
        if (LAB[r.y] !== undefined && (W >= 560 || r.y === 1976 || r.y === 2012 || r.y === 2018)) {
          var right = X(r.t) < W - 70;
          el("text", { class: "lab", x: X(r.t) + (right ? 9 : -9), y: Y(r.d) + 4, "text-anchor": right ? "start" : "end" }, s, String(r.y));
        }
      });
      if (title) title.textContent = S.label + ", " + rows.length + " races: " + sgn(b, 2) + "% per °F above " + KNOT + "°F";
    }
    seg(document.getElementById("era-seg"), function (k) { K = k; draw(); });
    onResize(draw); draw();
  })();

  // ------------------------------------------------------------ slope by position in the field
  (function () {
    var box = document.getElementById("slope-chart");
    if (!box) return;
    var read = document.getElementById("slope-read"), U = "pct";
    function draw() {
      var W = width(box), H = W < 560 ? 310 : 370, L = 52, R = 16, T = 30, B = 44;
      var rows = D.slopes.slice().sort(function (a, b) { return a.typical_min - b.typical_min; });
      var val = function (r, k) { return U === "pct" ? r[k] : r[k] / 100 * r.typical_min; };
      var top = Math.max.apply(null, rows.map(function (r) { return val(r, "beta_hi90"); }));
      var y1 = U === "pct" ? 0.7 : Math.ceil(top * 4 + 0.5) / 4, y0 = 0;
      var X = function (v) { return L + (v - 120) / (320 - 120) * (W - L - R); };
      var Y = function (v) { return T + (y1 - v) / (y1 - y0) * (H - T - B); };
      box.innerHTML = "";
      var s = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "img",
        "aria-label": "Heat slope above " + KNOT + " degrees for nine positions in the field, from men's 10th place to the 90th percentile, each with a 90 percent bootstrap interval." }, box);
      var st = U === "pct" ? 0.1 : (y1 > 1.5 ? 0.5 : 0.25);
      for (var v = 0; v <= y1 + 1e-9; v += st) {
        el("line", { class: "grid", x1: L, x2: W - R, y1: Y(v), y2: Y(v) }, s);
        el("text", { x: L - 6, y: Y(v) + 4, "text-anchor": "end" }, s, U === "pct" ? v.toFixed(1) + "%" : v.toFixed(2));
      }
      (W < 560 ? [120, 180, 240, 300] : [120, 150, 180, 210, 240, 270, 300]).forEach(function (t) { el("text", { x: X(t), y: H - B + 18, "text-anchor": "middle" }, s, hm(t)); });
      el("text", { x: W - R, y: H - 6, "text-anchor": "end" }, s, W < 560 ? "typical finish time" : "typical finish time of that position (2014 trend, cool day)");
      el("text", { x: 4, y: 12 }, s, U === "pct" ? "% of finish time per °F above " + KNOT + "°F" : "minutes per °F above " + KNOT + "°F");
      var marks = [];
      rows.forEach(function (r) {
        var x = X(r.typical_min), field = r.tier === "field";
        el("line", { class: "ci", x1: x, x2: x, y1: Y(val(r, "beta_lo90")), y2: Y(val(r, "beta_hi90")) }, s);
        var m = field ? el("circle", { class: "mk e2", cx: x, cy: Y(val(r, "beta_pct")), r: 6.5 }, s)
                      : el("rect", { class: "mk e1", x: x - 6, y: Y(val(r, "beta_pct")) - 6, width: 12, height: 12 }, s);
        m.setAttribute("tabindex", "0");
        m.setAttribute("aria-label", r.label + ", typical " + hm(r.typical_min) + ", " + r.beta_pct.toFixed(2) + " percent per degree, " + r.beta_min_at_typical.toFixed(2) + " minutes per degree");
        var show = function () {
          marks.forEach(function (q) { q.classList.remove("sel"); }); m.classList.add("sel");
          read.textContent = r.label + " (" + r.years + ", " + r.n_races + " races), typical " + hm(r.typical_min) + "  ·  " + r.beta_pct.toFixed(2) + "% per °F (90% interval " + r.beta_lo90.toFixed(2) + " to " + r.beta_hi90.toFixed(2) + ")  ·  " + r.beta_min_at_typical.toFixed(2) + " min per °F";
        };
        m.addEventListener("mouseenter", show); m.addEventListener("focus", show); m.addEventListener("click", show);
        marks.push(m);
      });
      var p50 = slopeOf("p50");
      el("text", { class: "lab", x: X(p50.typical_min) + 10, y: Y(val(p50, "beta_pct")) + 4 }, s, "median");
    }
    seg(document.getElementById("slope-seg"), function (k) { U = k; draw(); });
    onResize(draw); draw();
  })();

  // ------------------------------------------------------------ wind along the course
  (function () {
    var box = document.getElementById("wind-chart");
    if (!box) return;
    var read = document.getElementById("wind-read");
    var LAB = { 1994: 1, 2011: 1, 2018: 1, 2015: 1, 1943: 1, 2004: 1, 2017: 1 };
    function draw() {
      var W = width(box), H = W < 560 ? 280 : 330, L = 46, R = 12, T = 16, B = 36;
      var rows = D.years;
      var X = function (y) { return L + (y - 1939.5) / (2019.5 - 1939.5) * (W - L - R); };
      var Y = function (v) { return T + (17 - v) / 34 * (H - T - B); };
      var bw = Math.max(2, (W - L - R) / rows.length - 2);
      box.innerHTML = "";
      var s = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "img",
        "aria-label": "Wind along the course on each race day, 1940 to 2019. Bars above zero are tailwinds, below zero headwinds. 2018 had the strongest headwind, about 15 mph; 1994 and 2011 had tailwinds near 12 mph." }, box);
      [-15, -10, -5, 0, 5, 10, 15].forEach(function (v) {
        el("line", { class: "grid" + (v === 0 ? " zero" : ""), x1: L, x2: W - R, y1: Y(v), y2: Y(v) }, s);
        el("text", { x: L - 6, y: Y(v) + 4, "text-anchor": "end" }, s, (v > 0 ? "+" : "") + v);
      });
      for (var y = 1940; y <= 2019; y += (W < 560 ? 20 : 10)) el("text", { x: X(y), y: H - B + 18, "text-anchor": "middle" }, s, String(y));
      el("text", { x: L + 4, y: T + 2 }, s, "mph, tailwind ↑  headwind ↓");
      var marks = [];
      rows.forEach(function (r) {
        var v = r.twf, top = Y(Math.max(v, 0)), hgt = Math.max(1, Math.abs(Y(v) - Y(0)));
        var m = el("rect", { class: "bar " + (v >= 0 ? "tail" : "head"), x: X(r.y) - bw / 2, y: top, width: bw, height: hgt, tabindex: 0,
          "aria-label": r.y + ", " + (v >= 0 ? "tailwind " : "headwind ") + Math.abs(v).toFixed(1) + " mph, " + r.tf.toFixed(0) + " degrees" }, s);
        var show = function () {
          marks.forEach(function (q) { q.classList.remove("sel"); }); m.classList.add("sel");
          read.textContent = r.y + " (" + r.date + ")  ·  " + (v >= 0 ? "tailwind " : "headwind ") + Math.abs(v).toFixed(1) + " mph along the course  ·  " + r.tf.toFixed(1) + "°F, dew point " + r.dp.toFixed(0) + "°F" + (r.pr >= 1 ? "  ·  rain " + r.pr.toFixed(1) + " mm" : "");
        };
        m.addEventListener("mouseenter", show); m.addEventListener("focus", show); m.addEventListener("click", show);
        marks.push(m);
        if (LAB[r.y] && (W >= 560 || r.y === 2018 || r.y === 2011 || r.y === 1994)) {
          el("text", { class: "lab", x: X(r.y), y: v >= 0 ? top - 5 : top + hgt + 14, "text-anchor": "middle" }, s, String(r.y));
        }
      });
    }
    onResize(draw); draw();
  })();

  // ------------------------------------------------------------ holdout check
  (function () {
    var box = document.getElementById("hold-chart");
    if (!box) return;
    var read = document.getElementById("hold-read"), K = "p50";
    function draw() {
      var rows = D.holdout.filter(function (r) { return r.series === K; });
      var W = width(box), H = W < 560 ? 280 : 320, L = 46, R = 14, T = 18, B = 40;
      var all = []; rows.forEach(function (r) { all.push(r.dev_actual_pct, r.dev_pred_pct + 1.2816 * r.pred_sd_pct, r.dev_pred_pct - 1.2816 * r.pred_sd_pct); });
      var gs = (Math.max.apply(null, all) - Math.min.apply(null, all)) > 12 ? 4 : 2;
      var y1 = Math.ceil((Math.max.apply(null, all) + 0.5) / gs) * gs, y0 = Math.floor((Math.min.apply(null, all) - 0.5) / gs) * gs;
      var X = function (i) { return L + (i + 0.5) / rows.length * (W - L - R); };
      var Y = function (v) { return T + (y1 - v) / (y1 - y0) * (H - T - B); };
      box.innerHTML = "";
      var s = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, role: "img",
        "aria-label": "Holdout years 2015 to 2019 for the " + D.series[K].label.toLowerCase() + ": predicted and actual time against the five-year average, with 80 percent bands." }, box);
      for (var v = y0; v <= y1; v += gs) {
        el("line", { class: "grid" + (v === 0 ? " zero" : ""), x1: L, x2: W - R, y1: Y(v), y2: Y(v) }, s);
        el("text", { x: L - 6, y: Y(v) + 4, "text-anchor": "end" }, s, (v > 0 ? "+" : "") + v + "%");
      }
      el("text", { x: L + 4, y: T - 4 }, s, "against the 2015–2019 average");
      var marks = [];
      rows.forEach(function (r, i) {
        var x = X(i), bw = 1.2816 * r.pred_sd_pct;
        el("rect", { class: "band", x: x - 13, y: Y(r.dev_pred_pct + bw), width: 26, height: Math.max(1, Y(r.dev_pred_pct - bw) - Y(r.dev_pred_pct + bw)) }, s);
        el("line", { class: "pred", x1: x - 13, x2: x + 13, y1: Y(r.dev_pred_pct), y2: Y(r.dev_pred_pct) }, s);
        var m = el("circle", { class: "mk e2" + (r.in_80pct_band ? "" : " miss"), cx: x, cy: Y(r.dev_actual_pct), r: 6.5, tabindex: 0,
          "aria-label": r.year + ": predicted " + sgn(r.dev_pred_pct, 1) + " percent, actual " + sgn(r.dev_actual_pct, 1) + " percent" + (r.in_80pct_band ? ", inside the band" : ", outside the band") }, s);
        el("text", { x: x, y: H - B + 18, "text-anchor": "middle" }, s, String(r.year));
        var yw = YR[r.year];
        el("text", { class: "sub", x: x, y: H - B + 32, "text-anchor": "middle" }, s, Math.round(yw.tf) + "°F");
        var show = function () {
          marks.forEach(function (q) { q.classList.remove("sel"); }); m.classList.add("sel");
          read.textContent = r.year + "  ·  predicted " + sgn(r.dev_pred_pct, 1) + "%, actual " + sgn(r.dev_actual_pct, 1) + "%  ·  " + hms(r.actual_min) + "  ·  " + yw.tf.toFixed(0) + "°F, " + (yw.twf >= 0 ? "tailwind " : "headwind ") + Math.abs(yw.twf).toFixed(0) + " mph" + (r.in_80pct_band ? "" : "  ·  outside the 80% band");
        };
        m.addEventListener("mouseenter", show); m.addEventListener("focus", show); m.addEventListener("click", show);
        marks.push(m);
      });
    }
    var sel = document.getElementById("hold-series");
    if (sel) {
      D.slopes.forEach(function (r) { var o = h("option", { value: r.series }, sel, r.label); if (r.series === K) o.selected = true; });
      sel.addEventListener("change", function () { K = sel.value; draw(); });
    }
    onResize(draw); draw();
  })();

  // ------------------------------------------------------------ tables filled from the data file
  (function () {
    var t = document.getElementById("rob-body");
    if (t) {
      var order = ["men_10th", "men_25th", "men_100th", "men_1000th", "p10", "p25", "p50", "p75", "p90"];
      order.forEach(function (k) {
        var r = D.robustness.filter(function (x) { return x.series === k; })[0], tr = h("tr", {}, t);
        h("td", {}, tr, D.series[k].label);
        ["none", "linear", "era", "composition", "spline"].forEach(function (c) {
          h("td", { class: "num" + (c === "spline" ? " main" : "") }, tr, r[c] == null ? "n/a" : r[c].toFixed(2));
        });
      });
    }
    var c = document.getElementById("cv-body");
    if (c) {
      var name = { temp_f: "Dry-bulb temperature", dewpoint_f: "Dew point", heat_index_f: "Heat index", temp_plus_dew: "Temperature + dew point" };
      var best = {};
      D.selection.filter(function (r) { return r.stage === 1; }).forEach(function (r) {
        var k = r.heat_var + (r.knot === "" ? ":lin" : ":hinge");
        if (!best[k] || r.cv_rel_mean < best[k].cv_rel_mean) best[k] = r;
      });
      Object.keys(best).map(function (k) { return best[k]; }).sort(function (a, b) { return a.cv_rel_mean - b.cv_rel_mean; }).forEach(function (r) {
        var tr = h("tr", {}, c);
        h("td", {}, tr, name[r.heat_var]);
        h("td", {}, tr, r.knot === "" ? "straight line" : "flat, then rising above " + r.knot + "°");
        h("td", { class: "num" }, tr, sgn(100 * (1 - r.cv_rel_mean), 1).replace("+", "") + "%");
      });
      D.selection.filter(function (r) { return r.stage === 2; }).forEach(function (r) {
        var tr = h("tr", { class: "add" }, c);
        var nm = { tailwind_mph: "wind along the course", dewpoint_f: "dew point", rh_pct: "relative humidity", precip_mm: "rain", sw_rad_wm2: "sunshine", cloud_pct: "cloud cover" }[r.extra];
        h("td", {}, tr, "Temperature, plus " + nm);
        h("td", {}, tr, "flat, then rising above " + r.knot + "°");
        h("td", { class: "num" }, tr, sgn(100 * (1 - r.cv_rel_mean), 1).replace("+", "") + "%");
      });
    }
  })();

  // ------------------------------------------------------------ the model, in the browser
  var A = D.model.anchors.slice().sort(function (a, b) { return a.typ - b.typ; });
  function q(arr, p) { var s = arr.slice().sort(function (a, b) { return a - b; }), i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i); return s[lo] + (s[hi] - s[lo]) * (i - lo); }
  function effect(fin, temp, head) {
    var i = 0, j = 0, u = 0;
    if (fin <= A[0].typ) { i = j = 0; }
    else if (fin >= A[A.length - 1].typ) { i = j = A.length - 1; }
    else { j = 1; while (A[j].typ < fin) j++; i = j - 1; u = (fin - A[i].typ) / (A[j].typ - A[i].typ); }
    var ex = Math.max(temp - KNOT, 0), beta = (1 - u) * A[i].beta + u * A[j].beta;
    var le = beta * ex + (head != null ? D.model.wind.pct / 100 * head : 0);
    var n = Math.min(A[i].draws.length, A[j].draws.length, D.model.wind.draws.length), dr = [];
    for (var k = 0; k < n; k++) {
      var l = ((1 - u) * A[i].draws[k] + u * A[j].draws[k]) * ex + (head != null ? D.model.wind.draws[k] / 100 * head : 0);
      dr.push(fin * (Math.exp(l) - 1));
    }
    var e = fin * (Math.exp(le) - 1);
    return { e: e, lo: Math.min(q(dr, 0.05), e), hi: Math.max(q(dr, 0.95), e), pct: (1 - u) * A[i].pct + u * A[j].pct };
  }
  window.heatEffect = effect;

  // ------------------------------------------------------------ forecast tool
  (function () {
    var form = document.getElementById("fc-form");
    if (!form) return;
    var $ = function (id) { return document.getElementById(id); };
    var COURSE = [[42.2297, -71.5196], [42.2968, -71.2924], [42.35, -71.078]];
    var place = { name: "Boston Marathon course, Hopkinton to Boston", lat: COURSE.map(function (p) { return p[0]; }), lon: COURSE.map(function (p) { return p[1]; }), boston: true };

    function nextPatriotsDay(today) {
      for (var y = today.getFullYear(); y < today.getFullYear() + 2; y++) {
        var d = new Date(y, 3, 1), off = (8 - d.getDay()) % 7, m = new Date(y, 3, 1 + off + 14);
        if (m >= new Date(today.getFullYear(), today.getMonth(), today.getDate())) return m;
      }
    }
    function iso(d) { return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
    var today = new Date();
    $("fc-date").value = iso(nextPatriotsDay(today));
    function parseTime(s) { var p = String(s).trim().split(/[:.\s]+/).map(Number); if (p.some(isNaN) || p.length < 2 || p.length > 3) return null; return p[0] * 60 + p[1] + (p[2] || 0) / 60; }

    function setPlaceMode() {
      var other = $("fc-where").value === "other";
      $("fc-other").hidden = !other;
      $("fc-dir-row").hidden = !other;
      if (!other) place = { name: "Boston Marathon course, Hopkinton to Boston", lat: COURSE.map(function (p) { return p[0]; }), lon: COURSE.map(function (p) { return p[1]; }), boston: true };
      else if (place.boston) place = null;
      $("fc-place-note").textContent = other ? (place ? "Using " + place.name + "." : "Search for a town, then pick it from the list.") : "Three points on the course: Hopkinton, Wellesley, the Boylston Street finish.";
    }
    $("fc-where").addEventListener("change", setPlaceMode);

    $("fc-search").addEventListener("click", function () {
      var qy = $("fc-q").value.trim(), list = $("fc-results");
      if (qy.length < 2) return;
      list.innerHTML = ""; list.hidden = false;
      h("li", { class: "skel-line" }, list, " ");
      fetch("https://geocoding-api.open-meteo.com/v1/search?count=5&language=en&format=json&name=" + encodeURIComponent(qy))
        .then(function (r) { return r.json(); })
        .then(function (j) {
          list.innerHTML = "";
          (j.results || []).forEach(function (g) {
            var li = h("li", {}, list), b = h("button", { type: "button" }, li, g.name + (g.admin1 ? ", " + g.admin1 : "") + (g.country ? ", " + g.country : ""));
            b.addEventListener("click", function () {
              place = { name: b.textContent, lat: [g.latitude], lon: [g.longitude], boston: false };
              list.hidden = true; $("fc-place-note").textContent = "Using " + place.name + ".";
            });
          });
          if (!j.results) h("li", {}, list, "No match. Try a town name.");
        })
        .catch(function () { list.innerHTML = ""; h("li", {}, list, "Open-Meteo did not answer. Try again in a minute."); });
    });

    function mean(a) { var s = 0, n = 0; a.forEach(function (v) { if (v != null) { s += v; n++; } }); return n ? s / n : null; }
    function hourly(locs, h0, h1, bearing) {
      var T = [], Dp = [], U = [], V = [];
      locs.forEach(function (loc) {
        var H = loc.hourly;
        H.time.forEach(function (tm, i) {
          var hr = +tm.slice(11, 13);
          if (hr < h0 || hr > h1) return;
          T.push(H.temperature_2m[i]); Dp.push(H.dew_point_2m[i]);
          var ws = H.wind_speed_10m[i], wd = H.wind_direction_10m[i];
          if (ws != null && wd != null) { var to = (wd + 180) * Math.PI / 180; U.push(ws * Math.sin(to)); V.push(ws * Math.cos(to)); }
        });
      });
      var u = mean(U), v = mean(V), head = null;
      if (bearing != null && u != null) { var b = bearing * Math.PI / 180; head = -(u * Math.sin(b) + v * Math.cos(b)); }
      return { temp: mean(T), dew: mean(Dp), head: head, n: T.length };
    }

    function render(w, src, clim) {
      var fin = parseTime($("fc-time").value);
      var out = $("fc-out");
      out.innerHTML = "";
      if (fin == null || fin < 120 || fin > 480) { h("p", { class: "warn" }, out, "Enter a finish time between 2:00 and 8:00, like 3:45 or 4:12:30."); return; }
      var r = effect(fin, w.temp, w.head);
      h("p", { class: "lbl" }, out, "Expected slowdown");
      h("div", { class: "big" }, out, sgn(r.e, 1) + " min");
      h("p", { class: "delta" }, out, "90% interval " + sgn(r.lo, 1) + " to " + sgn(r.hi, 1) + " min. Finish about " + hms(fin + r.e) + ".");
      var dl = h("dl", { class: "wx" }, out);
      function row(k, v) { var d = h("div", {}, dl); h("dt", {}, d, k); h("dd", {}, d, v); }
      row("Temperature", w.temp.toFixed(1) + "°F (" + ((w.temp - 32) * 5 / 9).toFixed(1) + "°C)" + (clim ? ", typical" : ""));
      if (w.dew != null) row("Dew point", w.dew.toFixed(0) + "°F (shown only; the model does not use it)");
      row("Wind along the course", w.head == null ? "not used (no course direction)" : (w.head >= 0 ? "headwind " : "tailwind ") + Math.abs(w.head).toFixed(1) + " mph");
      row("Position in a Boston field", r.pct < 1 ? "front of the race (top 1%)" : "percentile " + Math.round(r.pct) + " (share of finishers faster)");
      h("p", { class: "src" }, out, src);
      var notes = [];
      if (w.temp <= KNOT) notes.push("At " + KNOT + "°F or cooler the model finds no heat cost. It also finds no gain from colder weather, and it has nothing to say about cold rain (2018 was its worst miss).");
      if (w.temp > 81) notes.push("Above 81°F only the 1976 race (87°F) is in the data, so this is an extrapolation.");
      if (!place.boston) notes.push("The rates were measured at Boston, on a Boston field, in April. Elsewhere they are a rough guide.");
      if (clim && clim.line) notes.push(clim.line);
      notes.forEach(function (n) { h("p", { class: "note" }, out, n); });
    }

    function skeleton() {
      var out = $("fc-out"); out.innerHTML = "";
      var sk = h("div", { class: "skel", "aria-hidden": "true" }, out);
      ["s1", "s2", "s3", "s3", "s3"].forEach(function (c) { h("span", { class: c }, sk); });
      h("p", { class: "src" }, out, "Asking Open-Meteo…");
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!place) { $("fc-place-note").textContent = "Search for a town and pick it first."; return; }
      var date = $("fc-date").value, start = +($("fc-start").value || "10:00").split(":")[0];
      if (!date) return;
      var h0 = start, h1 = Math.min(start + 6, 23);
      var bearing = place.boston ? D.model.bearing : ($("fc-dir").value === "" ? null : +$("fc-dir").value);
      var t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate()), d = new Date(date + "T00:00:00");
      var days = Math.round((d - t0) / 86400000);
      var lat = place.lat.join(","), lon = place.lon.join(",");
      var common = "&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto&start_date=" + date + "&end_date=" + date;
      var url, kind;
      if (days > 15) kind = "clim";
      else if (days >= -60) { kind = "fc"; url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat + "&longitude=" + lon + common; }
      else { kind = "past"; url = "https://archive-api.open-meteo.com/v1/archive?latitude=" + lat + "&longitude=" + lon + common; }

      if (kind === "clim" && place.boston) {
        var C = D.clim_boston, temps = C.temp.slice().sort(function (a, b) { return a - b; }), med = q(temps, 0.5);
        var fin = parseTime($("fc-time").value) || 225;
        var lo = effect(fin, q(temps, 0.1), null).e, hi = effect(fin, q(temps, 0.9), null).e;
        render({ temp: med, dew: q(C.dew, 0.5), head: null },
          "Climatology, not a forecast: " + date + " is more than 16 days away, beyond Open-Meteo's forecast range. The temperature is the median race-hour value of the 30 Boston races from 1990 to 2019 (ERA5, from this repo's data; no request was made).",
          { line: "In those 30 races the race-hour temperature ran from " + q(temps, 0.1).toFixed(0) + "°F to " + q(temps, 0.9).toFixed(0) + "°F (10th to 90th percentile), which for this time means " + sgn(lo, 1) + " to " + sgn(hi, 1) + " minutes. Check back within 16 days of the race for a forecast." });
        return;
      }
      skeleton();
      if (kind === "clim") {
        var md = date.slice(5), y = today.getFullYear() - 1;
        var curl = "https://archive-api.open-meteo.com/v1/archive?latitude=" + place.lat[0] + "&longitude=" + place.lon[0] +
          "&start_date=" + (y - 29) + "-01-01&end_date=" + y + "-12-31&daily=temperature_2m_max&temperature_unit=fahrenheit&timezone=auto";
        fetch(curl).then(function (r) { if (!r.ok) throw r; return r.json(); }).then(function (j) {
          var P = D.proxy, vals = [], target = new Date("2001-" + md + "T00:00:00");
          j.daily.time.forEach(function (tm, i) {
            var dd = new Date("2001-" + tm.slice(5) + "T00:00:00"), v = j.daily.temperature_2m_max[i];
            if (v != null && Math.abs(dd - target) <= 3 * 86400000) vals.push(P.a + P.b * v);
          });
          if (!vals.length) throw new Error("no data");
          var fin = parseTime($("fc-time").value) || 225, lo = effect(fin, q(vals, 0.1), null).e, hi = effect(fin, q(vals, 0.9), null).e;
          render({ temp: q(vals, 0.5), dew: null, head: null },
            "Climatology, not a forecast: " + date + " is beyond Open-Meteo's 16-day forecast range. Open-Meteo's historical archive gave the daily high within three days of this date in " + (y - 29) + " to " + y + " (" + vals.length + " days); each high was converted to a race-hour temperature with a line fitted on 80 Boston race days (typical error " + P.resid_sd_f.toFixed(1) + "°F).",
            { line: "Across those days the race-hour temperature ran from " + q(vals, 0.1).toFixed(0) + "°F to " + q(vals, 0.9).toFixed(0) + "°F (10th to 90th percentile): " + sgn(lo, 1) + " to " + sgn(hi, 1) + " minutes for this time." });
        }).catch(function () { $("fc-out").innerHTML = ""; h("p", { class: "warn" }, $("fc-out"), "Open-Meteo's archive did not answer. Try again in a minute."); });
        return;
      }
      fetch(url).then(function (r) { if (!r.ok) throw r; return r.json(); }).then(function (j) {
        var locs = Array.isArray(j) ? j : [j], w = hourly(locs, h0, h1, bearing);
        if (w.temp == null) throw new Error("empty");
        var when = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        render(w, (kind === "fc" ? "Forecast from Open-Meteo, fetched at " + when + ": " : "Reanalysis from Open-Meteo's historical archive: ") +
          "mean of hourly values from " + h0 + ":00 to " + h1 + ":00 local time" + (place.boston ? " at three points on the course." : " at " + place.name + "."), null);
      }).catch(function () { $("fc-out").innerHTML = ""; h("p", { class: "warn" }, $("fc-out"), "Open-Meteo did not answer, or has no data for that date and place. Try again in a minute."); });
    });
    setPlaceMode();
  })();
})();
