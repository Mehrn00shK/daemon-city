// Safar Bekheyr, extracted from safar-bekheyr.html by build.py
(function () {

// "Safar Bekheyr" — a 15 s 2D animation of the Iranian ritual of passing under the Qur'an
// and pouring water behind the traveller. Design space is 1280×720, rendered at 1920×1080.
const W = 1280, H = 720;
// HB: length of scene 3b (the family walking out through the door); the street scene is scripted
// on its own timeline and shifted by it. SLOW stretches play slower in real time
// (the daughter passing under the Qur'an, and her walk to the car): [start, end, speed]
const HB = 2.8, SCRIPT_END = 20.1 + HB;
const SLOW = [[3.7, 9.0, .65], [14.5 + HB, 16.0 + HB, .6]];
const DUR = SCRIPT_END + SLOW.reduce((sum, [a, b, k]) => sum + (b - a) * (1 / k - 1), 0);
function scriptTime(t) {
  let prev = 0;
  for (const [a, b, k] of SLOW) {
    if (t <= a - prev) return prev + t;
    t -= a - prev;
    if (t <= (b - a) / k) return a + t * k;
    t -= (b - a) / k; prev = b;
  }
  return prev + t;
}
const cv = document.createElement('canvas'); cv.width = 1280; cv.height = 720;
let ctx = cv.getContext('2d');   // reassigned temporarily by faded() to draw into an offscreen layer
const S = cv.width / W;

// Draws fn() as one layer at the given opacity, so a fading figure doesn't show its own
// overlapping parts through itself.
const layer = document.createElement('canvas'); layer.width = cv.width; layer.height = cv.height;
function faded(alpha, fn) {
  if (alpha <= 0) return;
  if (alpha >= .999) return fn();
  const main = ctx, lctx = layer.getContext('2d');
  lctx.setTransform(1, 0, 0, 1, 0, 0); lctx.clearRect(0, 0, layer.width, layer.height);
  lctx.setTransform(main.getTransform());
  ctx = lctx;
  try { fn(); } finally { ctx = main; }
  main.save(); main.setTransform(1, 0, 0, 1, 0, 0); main.globalAlpha = alpha; main.drawImage(layer, 0, 0); main.restore();
}

// ---------- math helpers ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = t => t * t * (3 - 2 * t);
const easeOut = t => 1 - (1 - t) * (1 - t);
const easeIO = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
function rng(seed) { return () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }; }

const C = {
  cream:'#f6ead7', wall:'#ecd6b3', wallDark:'#d8b98c', floor:'#a86f45', floorDark:'#8d5a36',
  wood:'#7a4528', woodLight:'#9a5d36', copper:'#c47a3c', copperLight:'#f0b872', copperDark:'#8e4f22',
  blue:'#1d5fae', blueDark:'#123f78', turq:'#2fa9c6', water:'#a8def2',
  green:'#1f6a4b', greenDark:'#154a34', gold:'#d9b257',
  skin:'#e7b993', skinDark:'#cf9c75', hair:'#2b1d16', ink:'#2a1d17',
  dress:'#2d3f7a', coat:'#cfae80', coatDark:'#b0895a', scarfM:'#f3e7d3', scarfD:'#b4523a', trousers:'#3a3340',
  suitcase:'#2f7f86', shirt:'#9fb8d6', shirtDark:'#7e9bbf', hairM:'#4a3428', hairF:'#7b736c', trousersF:'#3d4250', pink:'#ec8fa6', rose:'#d9415f', white:'#fff8ef', yellow:'#f7d774', leaf:'#5f9b62'
};

// ---------- drawing primitives ----------
function rr(x, y, w, h, r) { // rounded rect without ctx.roundRect, which older browsers lack
  if (w < 0) { x += w; w = -w; }
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath(); ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function circle(x, y, r, fill) { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill(); }
function ellipse(x, y, rx, ry, fill, rot = 0) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill(); }
function star8(x, y, r, fill) {
  ctx.beginPath();
  for (let i = 0; i < 16; i++) {
    const a = i * Math.PI / 8 - Math.PI / 2, rad = i % 2 ? r * .55 : r;
    ctx.lineTo(x + Math.cos(a) * rad, y + Math.sin(a) * rad);
  }
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
}
function flower(x, y, r, petal, center = C.yellow) {
  for (let i = 0; i < 5; i++) { const a = i * Math.PI * 2 / 5; circle(x + Math.cos(a) * r, y + Math.sin(a) * r, r * .75, petal); }
  circle(x, y, r * .6, center);
}
function leaves(x, y, s = 1) {
  ellipse(x - 16 * s, y + 8 * s, 15 * s, 6 * s, C.leaf, .5);
  ellipse(x + 15 * s, y - 9 * s, 14 * s, 5.5 * s, '#4f8a55', -.6);
}
function floral(x0, y0, x1, y1, step, seed) {
  const R = rng(seed), cols = [C.pink, C.white, '#f2c14e'];
  for (let y = y0; y < y1; y += step) for (let x = x0; x < x1; x += step) {
    const jx = (R() - .5) * step * .6, jy = (R() - .5) * step * .6;
    flower(x + jx, y + jy, step * .13, cols[Math.floor(R() * 3)]);
    if (R() < .5) ellipse(x + jx + step * .25, y + jy + step * .15, step * .12, step * .05, C.leaf, .6);
  }
}
function boteh(x, y, s, fill) { // paisley
  ctx.beginPath(); ctx.moveTo(x, y - s);
  ctx.bezierCurveTo(x + s * 1.1, y - s, x + s * 1.1, y + s, x, y + s);
  ctx.bezierCurveTo(x - s * 1.3, y + s, x - s * .5, y - s * .1, x - s * .2, y - s * 1.5);
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
}
function persianBorder(alpha) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha;
  for (const y of [0, H - 34]) {
    ctx.fillStyle = C.blueDark; ctx.fillRect(0, y, W, 34);
    ctx.fillStyle = C.gold; ctx.fillRect(0, y ? y : 31, W, 3);
    for (let x = 17; x < W + 17; x += 34) { star8(x, y + 17, 12, C.turq); circle(x, y + 17, 3.5, C.gold); }
  }
  ctx.restore();
}
function caption(fa, en, y, alpha, color = C.white) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.textAlign = 'center';
  ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 12;
  ctx.fillStyle = color;
  ctx.font = '700 46px Vazirmatn, Tahoma, sans-serif'; ctx.fillText(fa, W / 2, y);
  ctx.font = '400 22px "Segoe UI", Tahoma, sans-serif'; ctx.fillText(en, W / 2, y + 38);
  ctx.restore();
}

// ---------- props ----------
function quranClosed(x, y, w, h, rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  rr(-w / 2 + 4, -h / 2 + 6, w, h, 6); ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fill();
  rr(-w / 2, -h / 2, w, h, 6); ctx.fillStyle = C.green; ctx.fill();
  ctx.fillStyle = C.greenDark; ctx.fillRect(-w / 2, -h / 2 + 2, w * .07, h - 4);
  ctx.strokeStyle = C.gold; ctx.lineWidth = Math.max(1.5, w * .015);
  rr(-w / 2 + w * .1, -h / 2 + h * .1, w * .82, h * .8, 3); ctx.stroke();
  star8(w * .04, 0, h * .24, C.gold); circle(w * .04, 0, h * .1, C.green); circle(w * .04, 0, h * .045, C.gold);
  ctx.restore();
}
function quranOpen(x, y, w, h, o) {
  // o: 0 = closed cover on the right, 1 = fully open
  ctx.save(); ctx.translate(x, y);
  ellipse(0, h / 2 + 8, w * .55, 16, 'rgba(0,0,0,.18)');
  const page = (sx, flip) => {
    rr(sx, -h / 2, w / 2, h, 4); ctx.fillStyle = '#fbf3e1'; ctx.fill();
    ctx.strokeStyle = C.gold; ctx.lineWidth = 3; rr(sx + 18, -h / 2 + 18, w / 2 - 36, h - 36, 3); ctx.stroke();
    ctx.lineWidth = 1.2; rr(sx + 25, -h / 2 + 25, w / 2 - 50, h - 50, 2); ctx.stroke();
    // illegible decorative "text" lines
    ctx.strokeStyle = 'rgba(60,40,30,.35)'; ctx.lineWidth = 2;
    for (let i = 0; i < 9; i++) {
      const ly = -h / 2 + 48 + i * ((h - 90) / 8);
      ctx.beginPath();
      for (let k = 0; k <= 20; k++) {
        const lx = sx + 36 + k * (w / 2 - 72) / 20;
        ctx.lineTo(lx, ly + Math.sin(k * 1.7 + i * 2 + flip) * 2.5);
      }
      ctx.stroke();
    }
  };
  page(0, 0);
  const cw = Math.cos(Math.PI * o) * w / 2;          // flipping leaf width (+ right, − left)
  if (o > .5) page(-w / 2, 3);
  if (Math.abs(cw) > 1 && o < .97) {
    if (cw > 0) { rr(0, -h / 2, cw, h, 4); ctx.fillStyle = C.green; ctx.fill();
      ctx.strokeStyle = C.gold; ctx.lineWidth = 3; rr(cw * .1, -h / 2 + 16, cw * .8, h - 32, 3); ctx.stroke(); }
    else { rr(cw, -h / 2, -cw, h, 4); ctx.fillStyle = '#efe4cc'; ctx.fill(); }
  }
  ctx.fillStyle = 'rgba(120,80,40,.35)'; ctx.fillRect(-2, -h / 2, 4, h); // spine
  ctx.restore();
}
function bowlSide(cx, cy, r, tilt, fill) {
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(tilt);
  ellipse(0, 0, r, r * .28, C.blueDark);
  if (fill > .02) ellipse(0, r * .04 * (1 - fill), r * .9 * (.6 + .4 * fill), r * .22 * (.6 + .4 * fill), C.water);
  ctx.beginPath(); ctx.ellipse(0, 0, r, r * .78, 0, 0, Math.PI); ctx.fillStyle = C.blue; ctx.fill();
  ctx.save(); ctx.beginPath(); ctx.ellipse(0, 0, r, r * .78, 0, 0, Math.PI); ctx.clip();
  ctx.strokeStyle = C.turq; ctx.lineWidth = r * .1; ctx.beginPath(); ctx.ellipse(0, r * .05, r, r * .3, 0, 0, Math.PI); ctx.stroke();
  for (let i = 1; i < 8; i++) circle(Math.cos(Math.PI * i / 8) * r * .85, r * .38 + Math.sin(Math.PI * i / 8) * r * .1, r * .045, C.white);
  ctx.restore();
  ctx.strokeStyle = C.turq; ctx.lineWidth = r * .06; ctx.beginPath(); ctx.ellipse(0, 0, r, r * .28, 0, 0, Math.PI * 2); ctx.stroke();
  ellipse(-r * .45, r * .35, r * .12, r * .2, 'rgba(255,255,255,.25)', .4);
  ctx.restore();
}
function bowlTop(x, y, t) {
  ellipse(x + 8, y + 14, 120, 70, 'rgba(60,25,5,.35)');
  ellipse(x, y, 118, 70, C.blue);
  ctx.strokeStyle = C.turq; ctx.lineWidth = 8; ctx.beginPath(); ctx.ellipse(x, y, 104, 61, 0, 0, Math.PI * 2); ctx.stroke();
  for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; circle(x + Math.cos(a) * 111, y + Math.sin(a) * 66, 2.5, C.white); }
  const g = ctx.createRadialGradient(x - 20, y - 15, 5, x, y, 95);
  g.addColorStop(0, '#d8f3fb'); g.addColorStop(1, '#5fb7d8');
  ellipse(x, y, 94, 54, g);
  ctx.save(); ctx.beginPath(); ctx.ellipse(x, y, 94, 54, 0, 0, Math.PI * 2); ctx.clip();
  for (let k = 0; k < 3; k++) {
    const p = ((t * .55 + k / 3) % 1 + 1) % 1;
    ctx.strokeStyle = `rgba(255,255,255,${(1 - p) * .7})`; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(x + 10, y + 4, 94 * p, 54 * p, 0, 0, Math.PI * 2); ctx.stroke();
  }
  ellipse(x - 35, y - 18, 22, 7, 'rgba(255,255,255,.7)', -.2);
  ctx.restore();
}
function suitcase(x, y, s = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.strokeStyle = '#333'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-14, -110); ctx.lineTo(-14, -150); ctx.lineTo(14, -150); ctx.lineTo(14, -110); ctx.stroke();
  rr(-38, -112, 76, 106, 10); ctx.fillStyle = C.suitcase; ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.15)'; for (const lx of [-18, 0, 18]) ctx.fillRect(lx - 2, -104, 4, 90);
  circle(-26, -3, 6, '#222'); circle(26, -3, 6, '#222');
  ctx.restore();
}

// ---------- characters ----------
function ik(sx, sy, tx, ty, l1, l2, bend) {
  let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy);
  const md = l1 + l2 - .5;
  if (d > md) { tx = sx + dx / d * md; ty = sy + dy / d * md; d = md; }
  d = Math.max(d, Math.abs(l1 - l2) + 1);
  const a = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const ea = Math.atan2(dy, dx) + bend * a;
  return { ex: sx + Math.cos(ea) * l1, ey: sy + Math.sin(ea) * l1, hx: tx, hy: ty };
}

// Draws the mother, the father or the daughter. Feet at (x, y), f = facing (1 right, −1 left).
// handL / handR are world-space hand targets. Returns world-space hand positions.
function person(o) {
  const { x, y, s = 1, f = 1, type, walk = null, walkAmp = 1, eyesClosed = false, turn = 0 } = o;
  const nar = 1 - .4 * turn;                                   // turn: 0 = facing the viewer, 1 = side-on (profile)
  const M = type === 'mother', F = type === 'father', D = type === 'daughter';
  const top = M ? C.dress : F ? C.shirt : C.coat;
  const bob = walk != null ? -Math.abs(Math.sin(walk)) * 3 * walkAmp : 0;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ellipse(0, 0, (M ? 64 : 50) * nar, 9, 'rgba(0,0,0,.18)');
  ctx.translate(0, bob);

  // legs / feet
  const sw = walk != null ? Math.sin(walk) * .38 * walkAmp : 0;
  if (M) { ellipse(-15, -4, 13, 6, C.ink); ellipse(15, -4, 13, 6, C.ink); }
  else for (const [hx, a] of [[F ? -13 : -10, sw], [F ? 13 : 10, -sw]]) {
    const legTop = F ? -112 : -100, legLen = F ? 108 : 96;
    ctx.save(); ctx.translate(hx * nar, legTop); ctx.rotate(a);
    rr(-8, 0, 16, legLen, 6); ctx.fillStyle = F ? C.trousersF : C.trousers; ctx.fill();
    ellipse(f * 5, legLen + 1, 13, 6, C.ink);
    ctx.restore();
  }

  // body
  ctx.save(); ctx.scale(nar, 1); ctx.beginPath();
  if (M) {
    ctx.moveTo(-34, -228); ctx.quadraticCurveTo(-40, -180, -32, -150); ctx.lineTo(-64, -12);
    ctx.quadraticCurveTo(0, -2, 64, -12); ctx.lineTo(32, -150); ctx.quadraticCurveTo(40, -180, 34, -228);
    ctx.quadraticCurveTo(0, -240, -34, -228);
  } else if (F) {
    ctx.moveTo(-36, -228); ctx.lineTo(-38, -108); ctx.lineTo(38, -108); ctx.lineTo(36, -228); ctx.quadraticCurveTo(0, -238, -36, -228);
  } else {
    ctx.moveTo(-32, -228); ctx.lineTo(-36, -160); ctx.lineTo(-50, -88); ctx.quadraticCurveTo(0, -80, 50, -88);
    ctx.lineTo(36, -160); ctx.lineTo(32, -228); ctx.quadraticCurveTo(0, -238, -32, -228);
  }
  ctx.closePath(); ctx.fillStyle = top; ctx.fill(); ctx.clip();
  if (M) floral(-70, -240, 76, 0, 24, 7);
  else if (F) {
    ctx.fillStyle = C.shirtDark; ctx.fillRect(-1.5, -228, 3, 112);
    for (const by of [-205, -180, -155, -130]) circle(0, by, 2.2, C.white);
    ctx.beginPath(); ctx.moveTo(-14, -232); ctx.lineTo(0, -214); ctx.lineTo(14, -232); ctx.closePath(); ctx.fillStyle = C.white; ctx.fill();
    ctx.fillStyle = '#3a2a20'; ctx.fillRect(-40, -118, 80, 9); ctx.fillStyle = C.gold; ctx.fillRect(-5, -117, 10, 7);
  } else {
    ctx.fillStyle = C.coatDark; ctx.fillRect(-50, -163, 100, 8); ctx.fillRect(-2, -228, 4, 140);
    circle(-9, -200, 3, C.coatDark); circle(-9, -130, 3, C.coatDark);
    ctx.strokeStyle = '#6b4226'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(-28, -226); ctx.lineTo(44, -120); ctx.stroke();
  }
  ctx.restore();

  // neck, scarf, face
  ctx.fillStyle = C.skinDark; ctx.fillRect(-7, -250, 14, 26);
  const hx = f * (2 + 5 * turn), hy = -262, hair = M ? C.hairM : F ? C.hairF : C.hair;
  if (D) { // dark hair tied back in a ponytail, swinging behind the head
    const px = hx - f * 24, py = hy - 18, sw = Math.sin((walk ?? 0) * .5) * 4;
    ctx.beginPath(); ctx.moveTo(px, py - 6);
    ctx.quadraticCurveTo(px - f * 22, py + 10 + sw, px - f * (14 + sw), py + 52);
    ctx.quadraticCurveTo(px - f * 2, py + 30, px + f * 6, py + 4); ctx.closePath();
    ctx.fillStyle = hair; ctx.fill();
    circle(hx - f * 3, hy - 6, 25, hair);
    circle(px + f * 1, py - 1, 5, '#b4523a');                    // hair tie
  } else if (M) { // hair in a bun with a grey streak
    circle(hx - f * 4, hy - 4, 27, hair); circle(hx - f * 20, hy - 24, 13, hair);
    ctx.strokeStyle = '#a39488'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(hx - f * 4, hy - 4, 22, Math.PI * 1.15, Math.PI * 1.45); ctx.stroke();
  } else circle(hx - f * 2, hy - 6, 23, hair); // short greying hair
  const fx = hx + f * (5 + 5 * turn), fy = hy + 2;
  if (!D) ellipse(fx - f * (19 - 10 * turn), fy + 1, 4.5, 7, C.skinDark);
  ellipse(fx, fy, 19.5, 23, C.skin);
  ctx.save(); ctx.beginPath(); ctx.ellipse(fx, fy, 19.5, 23, 0, 0, Math.PI * 2); ctx.clip();
  ellipse(fx - f * 5, fy - (F ? 23 : 21), 23, F ? 8 : 10, hair);
  ctx.restore();
  if (D) { // side-swept fringe framing the face
    ctx.beginPath(); ctx.moveTo(fx - 20, fy - 6); ctx.quadraticCurveTo(fx - 18, fy - 27, fx + 2, fy - 25);
    ctx.quadraticCurveTo(fx + 20, fy - 24, fx + 21, fy - 4); ctx.quadraticCurveTo(fx + 8, fy - 20, fx - 20, fy - 6);
    ctx.fillStyle = hair; ctx.fill();
  }
  const ex = fx + f * (3 + 3 * turn), sp = 7.5 * (1 - .5 * turn);
  const eyes = [-sp, sp].filter(d => turn < .6 || d * f > 0);   // in profile only the near eye shows
  if (turn > .3) { ctx.beginPath(); ctx.moveTo(fx + f * 17, fy - 6); ctx.lineTo(fx + f * (20 + 5 * turn), fy + 3); ctx.lineTo(fx + f * 17, fy + 5); ctx.closePath(); ctx.fillStyle = C.skin; ctx.fill(); }
  ctx.strokeStyle = C.ink; ctx.lineWidth = 1.8;
  for (const d of eyes) {
    if (eyesClosed) { ctx.beginPath(); ctx.arc(ex + d, fy - 3, 3, .15 * Math.PI, .85 * Math.PI); ctx.stroke(); }
    else circle(ex + d, fy - 2, 2.4, C.ink);
  }
  ctx.strokeStyle = M ? '#5a4a40' : F ? '#5b524c' : C.hair;
  for (const d of eyes) { ctx.beginPath(); ctx.moveTo(ex + d - 4, fy - 9); ctx.quadraticCurveTo(ex + d, fy - 11.5, ex + d + 4, fy - 9); ctx.stroke(); }
  const ga = ctx.globalAlpha;
  ctx.globalAlpha = ga * .35; for (const d of eyes) circle(ex + d * 1.45, fy + 6, 4.5, '#e07b7b'); ctx.globalAlpha = ga;
  ctx.strokeStyle = '#9b4a3e'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(ex, fy + 7, 5, .2 * Math.PI, .8 * Math.PI); ctx.stroke();
  if (!D) { ctx.strokeStyle = 'rgba(120,70,50,.45)'; ctx.lineWidth = 1;
    for (const d of eyes) { ctx.beginPath(); ctx.arc(ex + d, fy + 1.5, 3.5, .2 * Math.PI, .8 * Math.PI); ctx.stroke(); } }
  if (F) {
    ellipse(ex - 4, fy + 4.5, 5.5, 2.8, '#5a524c', -.15); ellipse(ex + 4, fy + 4.5, 5.5, 2.8, '#5a524c', .15);
    ctx.strokeStyle = '#3a3330'; ctx.lineWidth = 1.6;
    for (const d of eyes) { ctx.beginPath(); ctx.arc(ex + d, fy - 2, 5.5, 0, Math.PI * 2); ctx.stroke(); }
    if (eyes.length > 1) { ctx.beginPath(); ctx.moveTo(ex - 2, fy - 2); ctx.lineTo(ex + 2, fy - 2); ctx.stroke(); }
  }

  // arms (two-bone IK towards the hand targets)
  const toLocal = p => p ? { x: (p.x - x) / s, y: (p.y - y) / s - bob } : null;
  const targets = [toLocal(o.handL) || { x: -44, y: -112 }, toLocal(o.handR) || { x: 44, y: -112 }];
  const out = [];
  [-1, 1].forEach((side, i) => {
    const sx = side * 30 * nar, sy = -222, t = targets[i];
    const a = ik(sx, sy, t.x, t.y, 62, 60, 1), b = ik(sx, sy, t.x, t.y, 62, 60, -1);
    const e = a.ex * side > b.ex * side ? a : b;
    ctx.strokeStyle = top; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(e.ex, e.ey); ctx.lineTo(e.hx, e.hy); ctx.stroke();
    if (M) for (const k of [.3, .7]) {
      flower(lerp(sx, e.ex, k), lerp(sy, e.ey, k), 2.2, C.pink);
      flower(lerp(e.ex, e.hx, k), lerp(e.ey, e.hy, k), 2.2, C.white);
    }
    circle(e.hx, e.hy, 8.5, C.skin);
    out.push({ x: x + e.hx * s, y: y + (e.hy + bob) * s });
  });
  ctx.restore();
  return { L: out[0], R: out[1] };
}

function profileHead(cx, cy, R, eyesClosed) { // daughter, facing left, big close-up
  ctx.beginPath(); ctx.moveTo(cx - R * .3, cy + R * .8); ctx.quadraticCurveTo(cx - R * .2, cy + R * 1.6, cx - R * .9, cy + R * 2.6);
  ctx.lineTo(cx + R * 2.2, cy + R * 2.6); ctx.quadraticCurveTo(cx + R * 1.6, cy + R * 1.2, cx + R * .9, cy + R * .6); ctx.closePath();
  ctx.fillStyle = C.coat; ctx.fill();
  ctx.fillStyle = C.skinDark; ctx.fillRect(cx - R * .25, cy + R * .6, R * .55, R * .6);
  ctx.beginPath(); ctx.moveTo(cx + R * .95, cy - R * .62);                     // ponytail hanging down her back
  ctx.quadraticCurveTo(cx + R * 1.75, cy - R * .2, cx + R * 1.45, cy + R * 1.55);
  ctx.quadraticCurveTo(cx + R * 1.2, cy + R * .6, cx + R * .85, cy - R * .2); ctx.closePath();
  ctx.fillStyle = C.hair; ctx.fill();
  circle(cx + R * .2, cy - R * .12, R * .95, C.hair);                         // hair pulled back
  circle(cx + R * .95, cy - R * .5, R * .1, '#b4523a');                       // hair tie
  ellipse(cx, cy, R * .82, R * .98, C.skin);
  ctx.beginPath(); ctx.moveTo(cx - R * .8, cy - R * .12); ctx.quadraticCurveTo(cx - R * 1.0, cy + R * .12, cx - R * .79, cy + R * .17);
  ctx.fillStyle = C.skin; ctx.fill();
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, R * .82, R * .98, 0, 0, Math.PI * 2); ctx.clip();
  ellipse(cx - R * .05, cy - R * .82, R * .9, R * .38, C.hair);
  ctx.restore();
  ctx.strokeStyle = C.ink; ctx.lineWidth = R * .035;
  if (eyesClosed) { ctx.beginPath(); ctx.arc(cx - R * .42, cy - R * .12, R * .11, .15 * Math.PI, .85 * Math.PI); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx - R * .52, cy - R * .06); ctx.lineTo(cx - R * .58, cy); ctx.stroke(); }
  else { circle(cx - R * .44, cy - R * .1, R * .06, C.ink); }
  ctx.strokeStyle = C.hair; ctx.beginPath(); ctx.moveTo(cx - R * .58, cy - R * .3); ctx.quadraticCurveTo(cx - R * .42, cy - R * .38, cx - R * .26, cy - R * .3); ctx.stroke();
  ctx.globalAlpha = .35; circle(cx - R * .3, cy + R * .25, R * .16, '#e07b7b'); ctx.globalAlpha = 1;
  ellipse(cx - R * .74, cy + R * .4, R * .07, R * .05, '#c0605a');
  ellipse(cx + R * .5, cy + R * .05, R * .12, R * .18, C.skinDark);
}

// ---------- scene 1 (0–3.5 s): the sini ----------
function sceneSini(t) {
  ctx.fillStyle = '#6e1f24'; ctx.fillRect(0, 0, W, H);
  for (let yy = 0, r = 0; yy < H + 60; yy += 60, r++) for (let xx = (r % 2) * 45; xx < W + 60; xx += 90) boteh(xx, yy, 13, 'rgba(217,178,87,.22)');

  const z = 1 + .07 * ease(seg(t, 0, 3));
  ctx.save(); ctx.translate(640, 400); ctx.scale(z, z); ctx.translate(-640, -400);
  const cx = 640, cy = 400;
  ellipse(cx + 10, cy + 20, 440, 236, 'rgba(0,0,0,.35)');
  let g = ctx.createRadialGradient(cx - 120, cy - 90, 30, cx, cy, 460);
  g.addColorStop(0, C.copperLight); g.addColorStop(.55, C.copper); g.addColorStop(1, C.copperDark);
  ellipse(cx, cy, 430, 228, g);
  ctx.strokeStyle = 'rgba(90,45,15,.55)'; ctx.lineWidth = 3;
  for (const k of [.93, .62]) { ctx.beginPath(); ctx.ellipse(cx, cy, 430 * k, 228 * k, 0, 0, Math.PI * 2); ctx.stroke(); }
  ctx.globalAlpha = .35;
  for (let i = 0; i < 28; i++) { const a = i / 28 * Math.PI * 2; star8(cx + Math.cos(a) * 430 * .78, cy + Math.sin(a) * 228 * .78, 9, C.copperDark); }
  ctx.globalAlpha = 1;
  const gx = lerp(380, 900, ease(seg(t, 0, 3))), gy = cy - 110;
  g = ctx.createRadialGradient(gx, gy, 0, gx, gy, 190);
  g.addColorStop(0, 'rgba(255,240,210,.5)'); g.addColorStop(1, 'rgba(255,240,210,0)');
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, 430, 228, 0, 0, Math.PI * 2); ctx.clip(); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();

  const R = rng(3);
  for (let i = 0; i < 26; i++) {
    const a = R() * Math.PI * 2, r = .3 + R() * .55;
    ellipse(cx + Math.cos(a) * 430 * r, cy + Math.sin(a) * 228 * r, 7, 4, R() < .5 ? C.pink : C.rose, R() * 3);
  }
  bowlTop(860, 350, t);
  for (const [fx, fy, c] of [[400, 470, C.pink], [440, 300, C.white], [760, 515, C.rose], [1000, 440, C.white],
                             [700, 262, C.pink], [540, 528, C.white], [975, 268, C.rose], [320, 385, C.rose]]) {
    leaves(fx, fy); flower(fx, fy, 13, c);
  }

  // mother's hands come in and lift the Qur'an
  const handIn = easeOut(seg(t, 1.3, 1.9)), lift = easeIO(seg(t, 1.95, 2.95));
  const qx = 555, qy = lerp(385, -170, lift);
  if (lift < 1) ellipse(qx + 6, 395, 110 * (1 - lift), 76 * (1 - lift), `rgba(60,25,5,${.3 * (1 - lift)})`);
  quranClosed(qx, qy, 210, 145, -.06);
  if (handIn > 0) for (const side of [-1, 1]) {
    const hx = qx + side * 106, hy = qy + 18 - (1 - handIn) * 420;
    const sx = hx + side * 80, sy = hy - 360;
    ctx.strokeStyle = C.dress; ctx.lineWidth = 46; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(hx + side * 6, hy - 30); ctx.stroke();
    for (let k = .15; k < .9; k += .18) flower(lerp(sx, hx, k) + side * 6, lerp(sy, hy - 30, k), 5, k * 10 % 2 < 1 ? C.pink : C.white);
    ellipse(hx, hy, 20, 26, C.skin, side * .3);
    ellipse(hx - side * 14, hy + 10, 7, 13, C.skinDark, side * .6);
  }
  ctx.restore();

  persianBorder(seg(t, .2, 1) * (1 - seg(t, 2.2, 2.9)));
  caption('پیش از سفر', 'Before a journey…', 640, seg(t, .5, 1.1) * (1 - seg(t, 2.2, 2.8)));
}

// ---------- the hallway room (shared by scene 2 and scene 3b) ----------
function hallRoom(t) {
  // walls: warm plaster with a faint star pattern, crown moulding and panelled wainscot
  let g = ctx.createLinearGradient(0, 0, 0, 542); g.addColorStop(0, '#f1e2c8'); g.addColorStop(1, '#e6d0ad');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 542);
  ctx.globalAlpha = .07;
  for (let yy = 60, r = 0; yy < 380; yy += 56, r++) for (let xx = (r % 2) * 38; xx < W; xx += 76) star8(xx, yy, 9, C.copperDark);
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#fbf3e4'; ctx.fillRect(0, 0, W, 22); ctx.fillStyle = '#d9c29c'; ctx.fillRect(0, 22, W, 5);
  ctx.fillStyle = '#efe3cc'; ctx.fillRect(0, 392, W, 140);
  ctx.fillStyle = '#d4bb92'; ctx.fillRect(0, 387, W, 7);
  ctx.strokeStyle = 'rgba(150,115,70,.35)'; ctx.lineWidth = 2;
  for (let x = 14; x < W; x += 112) ctx.strokeRect(x, 408, 92, 104);
  ctx.fillStyle = '#b08d62'; ctx.fillRect(0, 526, W, 16);

  // parquet floor, plank rows widening towards the viewer
  g = ctx.createLinearGradient(0, 542, 0, H); g.addColorStop(0, '#8a5a36'); g.addColorStop(1, '#a8714a');
  ctx.fillStyle = g; ctx.fillRect(0, 542, W, H - 542);
  ctx.strokeStyle = 'rgba(60,35,20,.25)'; ctx.lineWidth = 1;
  for (let y = 546, r = 0; y < H; r++) {
    const hgt = 9 + r * 2.4, step = 70 + r * 16;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    for (let x = (r % 2) * step / 2; x < W; x += step) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + hgt); ctx.stroke(); }
    y += hgt;
  }

  // pendant lamp
  ctx.strokeStyle = '#5a4630'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(300, 27); ctx.lineTo(300, 88); ctx.stroke();
  g = ctx.createRadialGradient(300, 120, 0, 300, 120, 170); g.addColorStop(0, 'rgba(255,225,160,.45)'); g.addColorStop(1, 'rgba(255,225,160,0)');
  ctx.fillStyle = g; ctx.fillRect(130, 40, 340, 260);
  ctx.beginPath(); ctx.moveTo(284, 88); ctx.lineTo(316, 88); ctx.lineTo(334, 124); ctx.lineTo(266, 124); ctx.closePath(); ctx.fillStyle = '#b8873e'; ctx.fill();
  ellipse(300, 125, 34, 5, '#fff1c9');

  // arched mirror with a gold frame above the console
  const arch = (x0, x1, top, bottom) => { const r = (x1 - x0) / 2; ctx.beginPath(); ctx.moveTo(x0, bottom); ctx.lineTo(x0, top + r); ctx.arc(x0 + r, top + r, r, Math.PI, 0); ctx.lineTo(x1, bottom); ctx.closePath(); };
  arch(42, 198, 132, 372); ctx.fillStyle = C.gold; ctx.fill();
  arch(54, 186, 144, 360); g = ctx.createLinearGradient(54, 144, 186, 360); g.addColorStop(0, '#e6eff2'); g.addColorStop(1, '#a9bec8'); ctx.fillStyle = g; ctx.fill();
  ctx.save(); arch(54, 186, 144, 360); ctx.clip();
  ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.moveTo(70, 360); ctx.lineTo(150, 144); ctx.lineTo(172, 144); ctx.lineTo(92, 360); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.beginPath(); ctx.moveTo(110, 360); ctx.lineTo(186, 160); ctx.lineTo(186, 200); ctx.lineTo(124, 360); ctx.fill();
  ctx.restore();
  star8(120, 128, 13, C.gold); circle(120, 128, 4, C.rose);

  // small framed landscape and a wall clock
  ctx.fillStyle = C.gold; ctx.fillRect(250, 160, 124, 88);
  g = ctx.createLinearGradient(0, 168, 0, 240); g.addColorStop(0, '#9cc9e8'); g.addColorStop(1, '#f4d9b3');
  ctx.fillStyle = g; ctx.fillRect(258, 168, 108, 72);
  ctx.fillStyle = '#8fa2bb'; ctx.beginPath(); ctx.moveTo(258, 240); ctx.lineTo(295, 196); ctx.lineTo(322, 222); ctx.lineTo(342, 204); ctx.lineTo(366, 240); ctx.fill();
  circle(1185, 205, 34, C.gold); circle(1185, 205, 29, '#fffaf0');
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; circle(1185 + Math.cos(a) * 23, 205 + Math.sin(a) * 23, 1.8, C.ink); }
  ctx.strokeStyle = C.ink; ctx.lineWidth = 2.5; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(1185, 205); ctx.lineTo(1185 + 13 * Math.cos(-1.9), 205 + 13 * Math.sin(-1.9)); ctx.stroke();
  ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(1185, 205); ctx.lineTo(1185 + 20 * Math.cos(t * .8), 205 + 20 * Math.sin(t * .8)); ctx.stroke();

  // coat hooks with a jacket and a patterned scarf, shoe cabinet below
  ctx.fillStyle = '#9a6a42'; ctx.fillRect(694, 236, 116, 10);
  for (const hx of [712, 752, 792]) circle(hx, 250, 4, C.gold);
  ctx.beginPath(); ctx.moveTo(712, 250); ctx.lineTo(690, 280); ctx.lineTo(694, 380); ctx.lineTo(732, 380); ctx.lineTo(734, 280); ctx.closePath(); ctx.fillStyle = '#3f5e52'; ctx.fill();
  ctx.fillStyle = '#c56b4a'; ctx.fillRect(784, 250, 16, 120); ctx.fillStyle = '#f0d58c';
  for (let y = 262; y < 366; y += 14) ctx.fillRect(784, y, 16, 3);
  ctx.fillStyle = '#c99b6b'; ctx.fillRect(688, 452, 128, 76); ctx.fillStyle = '#b3844f'; ctx.fillRect(688, 452, 128, 7);
  ctx.strokeStyle = 'rgba(80,50,25,.45)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(752, 462); ctx.lineTo(752, 526); ctx.stroke();
  circle(744, 494, 3, C.gold); circle(760, 494, 3, C.gold);
  ctx.fillStyle = '#b5583a'; ctx.fillRect(700, 430, 22, 22); circle(711, 420, 13, '#6f9f5b'); circle(703, 426, 8, '#5d8c4c');
  ellipse(785, 446, 18, 6, C.copper);
  ellipse(1050, 586, 20, 7, '#3a2a22'); ellipse(1076, 590, 20, 7, '#3a2a22');

  // tall potted plant beside the door
  ctx.fillStyle = '#b5583a'; ctx.beginPath(); ctx.moveTo(1158, 530); ctx.lineTo(1222, 530); ctx.lineTo(1212, 600); ctx.lineTo(1168, 600); ctx.closePath(); ctx.fill();
  for (const [a, l, c] of [[-2.0, 120, '#4f7d43'], [-1.7, 150, '#6f9f5b'], [-1.35, 140, '#5f8f4e'], [-1.1, 115, '#7fb068'], [-2.35, 100, '#5f8f4e'], [-.8, 95, '#4f7d43']]) {
    ctx.save(); ctx.translate(1190, 530); ctx.rotate(a + Math.PI / 2); ellipse(0, -l / 2, 18, l / 2, c); ctx.restore();
  }

  // door with morning light
  g = ctx.createLinearGradient(0, 170, 0, 542); g.addColorStop(0, '#cfe8f5'); g.addColorStop(1, '#fff2d6');
  ctx.fillStyle = g; ctx.fillRect(840, 170, 170, 372);
  circle(965, 300, 46, 'rgba(110,170,100,.55)'); circle(905, 330, 36, 'rgba(110,170,100,.45)');
  ctx.fillStyle = C.wood; ctx.fillRect(826, 156, 198, 16); ctx.fillRect(826, 156, 16, 386); ctx.fillRect(1008, 156, 16, 386);
  ctx.beginPath(); ctx.moveTo(1024, 172); ctx.lineTo(1120, 150); ctx.lineTo(1120, 572); ctx.lineTo(1024, 542); ctx.closePath();
  ctx.fillStyle = C.woodLight; ctx.fill();
  circle(1104, 370, 6, C.gold);
  ctx.beginPath(); ctx.moveTo(842, 542); ctx.lineTo(1008, 542); ctx.lineTo(1090, H); ctx.lineTo(700, H); ctx.closePath();
  ctx.fillStyle = 'rgba(255,240,200,.28)'; ctx.fill();

  // large Persian carpet in perspective (u across, v towards the viewer)
  const cp = (u, v) => [lerp(lerp(170, 70, v), lerp(930, 1030, v), u), lerp(574, 708, v)];
  const cpoly = (pts, fill) => { ctx.beginPath(); pts.forEach(([u, v], i) => { const [x, y] = cp(u, v); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); };
  const crect = (u0, v0, u1, v1, fill) => cpoly([[u0, v0], [u1, v0], [u1, v1], [u0, v1]], fill);
  const motif = (u, v, draw) => { const [x, y] = cp(u, v); ctx.save(); ctx.translate(x, y); ctx.scale(.8 + v * .35, (.8 + v * .35) * .42); draw(); ctx.restore(); };
  ctx.strokeStyle = '#f3ead6'; ctx.lineWidth = 1.5;
  for (let u = 0; u <= 1.001; u += .0125) {
    const [x, y] = cp(u, 1); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (u - .5) * 6, y + 9); ctx.stroke();
    const [x2, y2] = cp(u, 0); ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2, y2 - 4); ctx.stroke();
  }
  crect(0, 0, 1, 1, '#1f3566');
  for (let u = .03; u < 1; u += .04) for (const v of [.055, .945]) motif(u, v, () => flower(0, 0, 5, '#e9c46a', '#b5262f'));
  for (let v = .16; v < .86; v += .1) for (const u of [.03, .97]) motif(u, v, () => flower(0, 0, 5, '#e9c46a', '#b5262f'));
  crect(.06, .11, .94, .89, '#e3c27a');
  crect(.072, .13, .928, .87, '#2a7b82');
  crect(.082, .15, .918, .85, '#9e1f2b');
  for (let u = .12, i = 0; u < .9; u += .055) for (let v = .2; v < .82; v += .1, i++) {
    if (Math.abs(u - .5) < .2 && Math.abs(v - .5) < .33) continue;
    motif(u, v, i % 2 ? () => star8(0, 0, 9, '#c9473f') : () => flower(0, 0, 3.5, '#f1e4c8', '#1f3566'));
  }
  for (const [cu, cv, su, sv] of [[.082, .15, 1, 1], [.918, .15, -1, 1], [.082, .85, 1, -1], [.918, .85, -1, -1]]) {
    cpoly([[cu, cv], [cu + su * .13, cv], [cu, cv + sv * .26]], '#1f3566');
    cpoly([[cu, cv], [cu + su * .08, cv], [cu, cv + sv * .16]], '#e3c27a');
  }
  cpoly([[.5, .17], [.7, .5], [.5, .83], [.3, .5]], '#1f3566');
  cpoly([[.5, .24], [.63, .5], [.5, .76], [.37, .5]], '#e3c27a');
  cpoly([[.5, .31], [.57, .5], [.5, .69], [.43, .5]], '#9e1f2b');
  for (const v of [.15, .85]) motif(.5, v, () => star8(0, 0, 12, '#e3c27a'));
  motif(.5, .5, () => { star8(0, 0, 22, '#e3c27a'); circle(0, 0, 8, '#1f3566'); });
  g = ctx.createLinearGradient(0, 574, 0, 708); g.addColorStop(0, 'rgba(0,0,0,.12)'); g.addColorStop(1, 'rgba(255,240,210,.06)');
  cpoly([[0, 0], [1, 0], [1, 1], [0, 1]], g);

  // console table with the sini, bowl and flowers
  ctx.fillStyle = '#7a4a2c'; ctx.fillRect(20, 452, 200, 16); ctx.fillRect(34, 468, 10, 128); ctx.fillRect(196, 468, 10, 128);
  ctx.fillRect(34, 548, 172, 8);
  ctx.fillStyle = '#2a7b82'; ctx.fillRect(60, 530, 18, 18); ctx.fillStyle = '#c56b4a'; ctx.fillRect(80, 534, 14, 14); ctx.fillStyle = '#e3c27a'; ctx.fillRect(96, 528, 16, 20);
  ellipse(120, 450, 96, 15, C.copperDark); ellipse(120, 446, 92, 13, C.copper);
  leaves(70, 430, .7); flower(70, 430, 9, C.pink); flower(92, 438, 8, C.white); flower(50, 442, 7, C.rose);
  bowlSide(160, 428, 30, 0, 1);

}

// Qur'an in the mother's hands. Raised (up = 1) it is held flat above the head with the cover facing
// the ground: seen from below, the cover is foreshortened and the edge of the pages shows on top.
function heldQuran(hands, up) {
  const sq = lerp(1, .36, up), bw = lerp(70, 96, up), bh = lerp(50, 66, up);
  const qx = (hands.L.x + hands.R.x) / 2, qy = (hands.L.y + hands.R.y) / 2 - lerp(16, 8, up);
  ctx.save(); ctx.translate(qx, qy);
  if (up > .02) {
    const pg = 12 * up, top = -bh / 2 * sq - pg;
    rr(-bw / 2, top, bw, pg + 2, 2); ctx.fillStyle = '#f4ead2'; ctx.fill();
    ctx.strokeStyle = 'rgba(150,120,80,.5)'; ctx.lineWidth = .8;
    for (let k = 1; k < 5; k++) { ctx.beginPath(); ctx.moveTo(-bw / 2 + 2, top + k * pg / 5); ctx.lineTo(bw / 2 - 2, top + k * pg / 5); ctx.stroke(); }
  }
  ctx.scale(1, sq); quranClosed(0, 0, bw, bh, -.04 * (1 - up));
  ctx.restore();
  circle(hands.L.x, hands.L.y, 8.5, C.skin); circle(hands.R.x, hands.R.y, 8.5, C.skin);
}

// mother's hand targets: Qur'an at the chest, blended to above the head (raise) and lowered in front (lower)
function motherHands(mx, my, raise, lower) {
  const mix = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) });
  const chestL = { x: mx + 20, y: my - 175 }, chestR = { x: mx + 52, y: my - 175 };
  const upL = { x: mx + 38, y: my - 325 }, upR = { x: mx + 72, y: my - 325 };
  const lowL = { x: mx + 42, y: my - 205 }, lowR = { x: mx + 74, y: my - 205 };
  return { L: mix(mix(chestL, upL, raise), lowL, lower), R: mix(mix(chestR, upR, raise), lowR, lower) };
}

// ---------- scene 2 (3–9.4 s): by the front door, the daughter passes under the Qur'an three times ----------
function sceneHall(t) {
  hallRoom(t);
  const sway = Math.sin(t * 1.3) * 3;
  person({ x: 560, y: 600, s: 1.04, f: 1, type: 'father', handR: { x: 612 + sway, y: 430 } });
  const mx = 650, my = 612, raise = easeIO(seg(t, 3.1, 3.7)), lower = easeIO(seg(t, 8.85, 9.35));
  const mh = motherHands(mx, my, raise, lower);
  const hands = person({ x: mx, y: my, f: 1, type: 'mother', handL: mh.L, handR: mh.R });
  suitcase(848, 628, .95);

  // slow, calm passes: three gentle back-and-forth cycles under the raised Qur'an
  const p = seg(t, 3.7, 9.0), phase = 2 * Math.PI * 3 * p, moving = p > 0 && p < 1;
  const dx = 707 + 62 * Math.cos(phase), df = moving && Math.sin(phase) <= 0 ? 1 : -1;
  person({ x: dx, y: 630, f: df, type: 'daughter', walk: moving ? t * 6.5 : null, walkAmp: moving ? clamp(Math.abs(Math.sin(phase)) * 1.4 + .25) : 0 });
  heldQuran(hands, raise * (1 - lower));

  // count the three passes with soft gold dots
  const passes = Math.min(3, Math.floor(p * 3 + .5));
  for (let i = 0; i < 3; i++) {
    ctx.globalAlpha = seg(t, 3.7, 4.0) * (1 - seg(t, 8.9, 9.3));
    circle(677 + i * 28, 110, 8, i < passes ? C.gold : 'rgba(217,178,87,.3)');
  }
  ctx.globalAlpha = 1;
}

// ---------- scene 3b (u = 0–HB s, after the kiss): all three walk out through the front door ----------
function sceneHallOut(u) {
  hallRoom(11.4 + u);
  const DOOR = 925;
  // each walks from their spot into the doorway and fades out as they step through it
  const walker = (x0, u0, u1) => {
    const k = easeIO(seg(u, u0, u1)), x = lerp(x0, DOOR, k);
    return { x, fade: seg(x, DOOR - 55, DOOR), moving: k > 0 && k < 1 };
  };
  const fa = walker(560, 1.0, 2.6), mo = walker(650, .55, 2.0), da = walker(769, .1, 1.3);
  const stepOut = (w, fn) => faded(1 - w.fade, () => fn(-8 * w.fade));
  stepOut(fa, dy => person({ x: fa.x, y: 600 + dy, s: 1.04, f: 1, type: 'father', walk: fa.moving ? u * 6 + 1 : null }));
  stepOut(mo, dy => {
    const mh = motherHands(mo.x, 612 + dy, 0, 1);
    heldQuran(person({ x: mo.x, y: 612 + dy, f: 1, type: 'mother', walk: mo.moving ? u * 6 : null, handL: mh.L, handR: mh.R }), 0);
  });
  stepOut(da, dy => {
    const sx = Math.max(848, da.x + 58), pulling = da.x + 58 >= 848;
    person({ x: da.x, y: 630 + dy, f: 1, type: 'daughter', walk: da.moving ? u * 6.5 : null, handR: pulling ? { x: sx - 10, y: 487 + dy } : null });
    suitcase(sx, 628 + dy, .95);
  });
}

// ---------- scene 3 (9.4–11.4 s): kissing the Qur'an at the door ----------
function sceneKiss(t) {
  let g = ctx.createRadialGradient(560, 380, 50, 640, 360, 820);
  g.addColorStop(0, '#f6e1c6'); g.addColorStop(1, '#b98a5e');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const R = rng(11);
  for (let i = 0; i < 18; i++) circle(R() * W, R() * H, 20 + R() * 60, `rgba(255,236,200,${.08 + R() * .12})`);

  const o = easeIO(seg(t, 9.45, 9.95));
  const bx = 560, by = 420, bw = 440, bh = 280;
  quranOpen(bx, by, bw, bh, o);
  for (const side of [-1, 1]) {
    const hx = bx + side * (bw / 2 - 20), hy = by + bh / 2 - 6;
    ctx.strokeStyle = C.dress; ctx.lineWidth = 50; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(hx + side * 70, H + 60); ctx.lineTo(hx + side * 10, hy + 40); ctx.stroke();
    for (let k = .2; k < .9; k += .22) flower(lerp(hx + side * 70, hx + side * 10, k), lerp(H + 60, hy + 40, k), 5, k * 10 % 2 < 1 ? C.pink : C.white);
    ellipse(hx, hy, 24, 20, C.skin);
    ellipse(hx - side * 4, hy - 16, 9, 18, C.skin, side * .2);
  }

  // daughter leans in, kisses the page, and leans back
  const lean = easeIO(seg(t, 9.95, 10.45)), back = easeIO(seg(t, 10.85, 11.35)), Rh = 105;
  const kissX = 690 + .76 * Rh, kissY = 400 - .4 * Rh;
  const cx = lerp(lerp(1060, kissX, lean), 900, back), cy = lerp(lerp(300, kissY, lean), 330, back);
  profileHead(cx, cy, Rh, t > 9.8 && t < 11.1);

  const k = seg(t, 10.45, 11.1);
  if (k > 0 && k < 1) {
    ctx.globalAlpha = Math.sin(k * Math.PI);
    for (let i = 0; i < 7; i++) {
      const a = i / 7 * Math.PI * 2 + k * 2;
      star8(690 + Math.cos(a) * (20 + k * 70), 400 + Math.sin(a) * (20 + k * 50) - k * 40, 7, C.gold);
    }
    ctx.globalAlpha = 1;
  }
}

// ---------- scene 4 (local 11.4–20.1 s, shifted by HB): goodbyes, car, water ----------
function sceneStreet(t) {
  let g = ctx.createLinearGradient(0, 0, 0, 400); g.addColorStop(0, '#9cc9e8'); g.addColorStop(1, '#fbe3c4');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 400);
  g = ctx.createRadialGradient(935, 300, 0, 935, 300, 240);
  g.addColorStop(0, 'rgba(255,248,225,1)'); g.addColorStop(.17, 'rgba(255,236,190,.9)'); g.addColorStop(1, 'rgba(255,236,190,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 420);

  // Alborz mountains
  const peaks = [[0, 330], [120, 292], [230, 320], [360, 250], [470, 300], [600, 240], [720, 290], [840, 228], [960, 285], [1080, 246], [1200, 300], [1280, 282]];
  ctx.fillStyle = '#aab7ca'; ctx.beginPath(); ctx.moveTo(0, 400); for (const q of peaks) ctx.lineTo(q[0], q[1]); ctx.lineTo(W, 400); ctx.fill();
  ctx.fillStyle = '#f4f6fa';
  for (const [px, py] of [[360, 250], [600, 240], [840, 228], [1080, 246]]) {
    ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px - 28, py + 22); ctx.lineTo(px - 8, py + 16); ctx.lineTo(px + 6, py + 24); ctx.lineTo(px + 26, py + 20); ctx.closePath(); ctx.fill();
  }

  // ---- a modern Tehran residential street (kooche) in simple 3D perspective ----
  // world units are metres: X across the street, Y up, Z away from the camera
  const VX = 920, VY = 400, FOC = 1000, CAM = 1.29;            // vanishing point, focal length, eye height
  const pr = (X, Y, Z) => [VX + FOC * X / Z, VY + FOC * (CAM - Y) / Z];
  const poly = (pts, fill) => { ctx.beginPath(); ctx.moveTo(...pts[0]); for (const q of pts.slice(1)) ctx.lineTo(...q); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); };
  const strip = (x0, x1, fill) => poly([pr(x0, 0, 3), pr(x1, 0, 3), pr(x1, 0, 600), pr(x0, 0, 600)], fill);
  const LF = -5.4, RF = 6.6;                                     // building fronts left / right

  // pavements, asphalt, jube water channels and curbs
  ctx.fillStyle = '#cbb89c'; ctx.fillRect(0, VY - 1, W, H - VY + 1);
  ctx.strokeStyle = 'rgba(90,70,50,.14)'; ctx.lineWidth = 1;
  for (let z = 3.5; z < 90; z *= 1.12) for (const [a, b] of [[LF, -2.3], [4.3, RF]]) { ctx.beginPath(); ctx.moveTo(...pr(a, 0, z)); ctx.lineTo(...pr(b, 0, z)); ctx.stroke(); }
  strip(-1.8, 3.8, '#5d5c61');
  strip(-2.3, -1.8, '#59666c'); strip(3.8, 4.3, '#59666c');
  strip(-2.12, -1.98, 'rgba(150,205,228,.55)'); strip(3.98, 4.12, 'rgba(150,205,228,.55)');
  for (const x of [-2.36, -1.86, 3.8, 4.3]) strip(x, x + .06, '#ece6da');

  // apartment buildings with windows, glass balconies, plants, AC units, garage doors and entrances
  const glassCols = ['#8fb3cf', '#a9c6db', '#6f93b3', '#b9d3e3', '#7d9fb9', '#f1d7a2'];
  const building = (side, b, idx) => {
    const X = side < 0 ? LF : RF, out = -side, Hh = b.floors * 3.2 + .7, len = b.z1 - b.z0;
    const F3 = (y, z, d = 0) => pr(X + out * d, y, z);
    poly([pr(X, 0, b.z0), pr(X + side * 14, 0, b.z0), pr(X + side * 14, Hh, b.z0), pr(X, Hh, b.z0)], b.end);
    poly([F3(0, b.z0), F3(0, b.z1), F3(Hh, b.z1), F3(Hh, b.z0)], b.wall);
    poly([F3(0, b.z0), F3(0, b.z1), F3(1, b.z1), F3(1, b.z0)], b.base);
    poly([F3(Hh - .45, b.z0), F3(Hh - .45, b.z1), F3(Hh, b.z1), F3(Hh, b.z0)], b.accent);
    const za = b.z0 + len * .12, zb = b.z0 + len * .48;
    poly([F3(0, za), F3(0, zb), F3(2.5, zb), F3(2.5, za)], '#77736d');
    ctx.strokeStyle = 'rgba(0,0,0,.18)'; ctx.lineWidth = 1;
    for (let y = .3; y < 2.5; y += .3) { ctx.beginPath(); ctx.moveTo(...F3(y, za)); ctx.lineTo(...F3(y, zb)); ctx.stroke(); }
    const ea = b.z0 + len * .6, eb = b.z0 + len * .74;
    poly([F3(0, ea), F3(0, eb), F3(2.6, eb), F3(2.6, ea)], '#2f3c48');
    poly([F3(.1, ea + .15), F3(.1, eb - .15), F3(2.45, eb - .15), F3(2.45, ea + .15)], '#5f7f97');
    poly([F3(2.8, ea - .3), F3(2.8, eb + .3), F3(2.8, eb + .3, .9), F3(2.8, ea - .3, .9)], b.accent);
    const bays = Math.max(2, Math.round(len / 3.4));
    for (let f = 1; f < b.floors; f++) for (let k = bays - 1; k >= 0; k--) {
      const y0 = f * 3.2 + .3, wa = b.z0 + len * (k + .15) / bays, wb = b.z0 + len * (k + .85) / bays;
      poly([F3(y0 + .4, wa), F3(y0 + .4, wb), F3(y0 + 2.7, wb), F3(y0 + 2.7, wa)], '#38424c');
      poly([F3(y0 + .52, wa + .1), F3(y0 + .52, wb - .1), F3(y0 + 2.58, wb - .1), F3(y0 + 2.58, wa + .1)], glassCols[(idx * 7 + f * 3 + k * 5) % glassCols.length]);
      ctx.strokeStyle = '#38424c'; ctx.lineWidth = 1.5;
      const wm = (wa + wb) / 2; ctx.beginPath(); ctx.moveTo(...F3(y0 + .5, wm)); ctx.lineTo(...F3(y0 + 2.6, wm)); ctx.stroke();
      if (!b.balc || (k + f) % 2) continue;
      const ba = wa - .25, bb = wb + .25, d = 1.2;
      poly([F3(y0, ba), F3(y0, bb), F3(y0, bb, d), F3(y0, ba, d)], b.accent);
      poly([F3(y0 - .22, ba, d), F3(y0 - .22, bb, d), F3(y0, bb, d), F3(y0, ba, d)], b.accent);
      if ((k * 3 + f) % 3 === 0) {
        const [px, py] = F3(y0 + .55, ba + .5, d - .4), r = FOC / (ba + .5) * .4;
        circle(px, py, r, '#5d8f4f'); circle(px + r * .5, py - r * .45, r * .7, '#76a865');
      }
      if ((k + 2 * f) % 4 === 1) poly([F3(y0 + .1, bb - .9, .25), F3(y0 + .1, bb - .2, .25), F3(y0 + .7, bb - .2, .25), F3(y0 + .7, bb - .9, .25)], '#ecebe7');
      poly([F3(y0, ba, 0), F3(y0, ba, d), F3(y0 + 1.05, ba, d), F3(y0 + 1.05, ba, 0)], 'rgba(185,210,222,.5)');
      poly([F3(y0, ba, d), F3(y0, bb, d), F3(y0 + 1.05, bb, d), F3(y0 + 1.05, ba, d)], 'rgba(185,210,222,.55)');
      ctx.strokeStyle = '#2f3438'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(...F3(y0 + 1.05, ba, 0)); ctx.lineTo(...F3(y0 + 1.05, ba, d)); ctx.lineTo(...F3(y0 + 1.05, bb, d)); ctx.stroke();
    }
  };
  const styles = [
    { wall: '#ece6dc', base: '#bdb3a4', accent: '#5f646b', end: '#d6cec2', balc: true },   // white travertine
    { wall: '#d9d6d1', base: '#9d9993', accent: '#a0714a', end: '#c4c0ba', balc: true },   // light grey with wood
    { wall: '#e6d5bb', base: '#b49c7c', accent: '#4e5359', end: '#cfbfa5', balc: true },   // warm stone
    { wall: '#c9ccd0', base: '#8c9096', accent: '#e8e4dc', end: '#b3b6ba', balc: false }   // grey composite panels
  ];
  const Lb = [[3, 15, 5], [15.4, 26, 4], [26.4, 37, 6], [37.4, 49, 5], [49.4, 63, 4], [63.4, 80, 5], [80.4, 100, 6], [100.4, 140, 5]];
  const Rb = [[3, 13, 6], [13.4, 25, 5], [25.4, 36, 4], [36.4, 50, 6], [50.4, 64, 5], [64.4, 82, 4], [82.4, 104, 5], [104.4, 140, 6]];
  for (let i = Lb.length - 1; i >= 0; i--) {
    building(-1, { ...styles[i % 4], z0: Lb[i][0], z1: Lb[i][1], floors: Lb[i][2] }, i);
    building(1, { ...styles[(i + 2) % 4], z0: Rb[i][0], z1: Rb[i][1], floors: Rb[i][2] }, i + 20);
  }

  // plane trees (chenar) and street lamps, drawn later in depth order together with the car
  const tree = (X, Z, seed) => {
    const k = FOC / Z, [bx, by] = pr(X, 0, Z), [tx, ty] = pr(X, 4.6, Z), R = rng(seed);
    ctx.beginPath(); ctx.moveTo(bx - .2 * k, by); ctx.lineTo(tx - .12 * k, ty); ctx.lineTo(tx + .12 * k, ty); ctx.lineTo(bx + .2 * k, by); ctx.closePath();
    ctx.fillStyle = '#b5a68a'; ctx.fill();
    for (let i = 0; i < 7; i++) { const v = R(); ellipse(lerp(bx, tx, v) + (R() - .5) * .18 * k * (1 - v * .4), lerp(by, ty, v), .06 * k, .13 * k, R() < .5 ? '#8c866c' : '#d8ceb4'); }
    ctx.strokeStyle = '#9d907a'; ctx.lineWidth = Math.max(1, .08 * k); ctx.lineCap = 'round';
    for (const [dx, dy] of [[-1.3, 6.3], [1.2, 6.7], [0, 7.4]]) { ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(...pr(X + dx, dy, Z)); ctx.stroke(); }
    const greens = ['#5f8f4e', '#6f9f5b', '#7fb068', '#4f7d43'];
    for (let i = 0; i < 10; i++) { const [cx, cy] = pr(X + (R() - .5) * 3.8, 6.2 + R() * 2.6, Z); circle(cx, cy, (1.1 + R() * .9) * k, greens[i % 4]); }
  };
  const lamp = (X, Z) => {
    const k = FOC / Z, [bx, by] = pr(X, 0, Z), [tx, ty] = pr(X, 6.2, Z), [ax, ay] = pr(X + 1.4, 6.2, Z);
    ctx.strokeStyle = '#3d4248'; ctx.lineWidth = Math.max(1, .12 * k); ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(tx, ty); ctx.lineTo(ax, ay); ctx.stroke();
    ellipse(ax, ay + .06 * k, .35 * k, .1 * k, '#2f3338');
  };
  const items = [];
  [7.5, 12.5, 18, 24, 31, 40, 52, 66, 85].forEach((z, i) => items.push({ z, draw: () => tree(-2.7, z, i + 1) }));
  [7.3, 12.3, 17.8, 24.3, 31.3, 40.3, 52.3, 66.3, 85.3].forEach((z, i) => items.push({ z, draw: () => tree(4.65, z, i + 40) }));
  [10, 28, 46, 70].forEach(z => items.push({ z, draw: () => lamp(-2.0, z) }));

  const mixP = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) });
  const ps = y => (y - 400) / 305 * 1.3;              // perspective scale of a person standing at ground line y

  // daughter: hugs her father face to face and kisses his cheek, then her mother, then walks to the car and gets in
  const hugF = easeIO(seg(t, 11.35, 11.6)) * (1 - easeIO(seg(t, 12.55, 12.8)));
  const hugM = easeIO(seg(t, 13.25, 13.5)) * (1 - easeIO(seg(t, 14.3, 14.55)));
  const kissF = Math.sin(seg(t, 11.95, 12.45) * Math.PI), kissM = Math.sin(seg(t, 13.7, 14.2) * Math.PI);
  const step = easeIO(seg(t, 12.6, 13.3)), walk = easeIO(seg(t, 14.5, 16.0)), getIn = seg(t, 16.0, 16.35);
  const dX = lerp(lerp(lerp(222, 412, step) - 10 * kissF + 10 * kissM, 873, walk), 951, getIn), dY = lerp(lerp(712, 600, walk), 598, getIn);
  const dMoving = (step > 0 && step < 1) || (walk > 0 && walk < 1);
  const dFace = t < 12.6 ? -1 : t < 13.25 ? 1 : t < 14.5 ? -1 : 1;
  const drawDaughter = () => {
    if (getIn >= 1) return;
    const s = ps(dY), rest = side => ({ x: dX + side * 44 * s, y: dY - 112 * s });
    const hL = mixP(mixP(rest(-1), { x: 108, y: 470 }, hugF), { x: 318, y: 470 }, hugM);
    // her suitcase waits beside her during the goodbyes; she pulls it to the car and takes it in with her
    const pulling = t >= 14.5, ss = (pulling ? s : ps(712)) * .95;
    const sx = pulling ? dX + 58 * s : 489, sy = pulling ? dY : 712;
    const hR = pulling ? { x: sx - 10 * ss, y: sy - 148 * ss }
                       : mixP(mixP(rest(1), { x: 128, y: 505 }, hugF), { x: 338, y: 505 }, hugM);
    faded(1 - getIn, () => {
      person({ x: dX, y: dY, s, f: dFace, turn: Math.max(hugF, hugM), type: 'daughter', walk: dMoving ? t * 7 : null,
        eyesClosed: kissF > .3 || kissM > .3, handL: hL, handR: hR });
      suitcase(sx, sy, ss);
    });
  };

  // the car: she gets in (small bounce), waves from the rear window, then it drives away
  const u = Math.pow(seg(t, 17.1, 20.0), 1.7), bump = Math.sin(seg(t, 16.15, 16.45) * Math.PI) * 3;
  const carZ = 6.45 * Math.exp(4.4 * u);                      // drives along the middle of the street (X = 1 m)
  const carY = VY + FOC * CAM / carZ, carS = FOC / carZ / 133, carX = VX + FOC / carZ;
  items.push({ z: carZ, draw: () => {
    for (let i = 0; i < 4; i++) {
      const pk = (t * 1.5 + i / 4) % 1;
      if (u > 0) ellipse(carX - 60 * carS - pk * 30 * carS, carY - 18 * carS - pk * 30 * carS, (10 + pk * 22) * carS, (8 + pk * 16) * carS, `rgba(220,220,220,${(1 - pk) * .35})`);
    }
    carRear(carX, carY + bump, carS, t, t > 16.2, seg(t, 16.45, 16.7) * (1 - seg(t, 18.4, 18.7)));
  } });
  if (t >= 15.6) items.push({ z: FOC * CAM / Math.max(1, dY - VY) + .02, draw: drawDaughter });
  items.sort((a, b) => b.z - a.z).forEach(it => it.draw());

  // father: hugs her, then waves goodbye
  const fx0 = 115, fs = 1.27, waveIn = easeIO(seg(t, 16.35, 16.7));
  const restF = { x: fx0 + 44 * fs, y: 690 - 112 * fs };
  person({ x: fx0, y: 690, s: fs, f: 1, turn: hugF, type: 'father',
    handR: mixP(restF, { x: 242, y: 478 }, hugF),
    handL: { x: lerp(fx0 - 44 * fs, fx0 - 62 * fs + Math.sin(t * 8) * 12, waveIn), y: lerp(690 - 112 * fs, 690 - 300 * fs, waveIn) } });

  // mother: hugs her face to face holding the bowl at her side, then throws the water once the car moves
  const mx = 330, my = 705, ms = 1.3;
  const toChest = easeIO(seg(t, 14.45, 14.95)), thr = easeIO(seg(t, 17.5, 17.95)), rel = easeIO(seg(t, 18.5, 19.1));
  const P = (dx, dy) => ({ x: mx + dx * ms, y: my + dy * ms });
  const pose = (a, b, c) => mixP(mixP(a, b, thr), c, rel);
  const hL = pose(mixP(P(-52, -140), P(18, -175), toChest), P(90, -232), P(28, -150));
  const hR = pose(mixP(mixP(P(44, -112), { x: 432, y: 480 }, hugM), P(50, -175), toChest), P(118, -224), P(60, -150));
  const hands = person({ x: mx, y: my, s: ms, f: 1, turn: hugM, type: 'mother', handL: hL, handR: hR });
  const tilt = lerp(lerp(0, 1.05, thr), .25, rel), fill = 1 - seg(t, 17.75, 18.2);
  const bx = lerp(hands.L.x - 6 * ms, (hands.L.x + hands.R.x) / 2, toChest);
  const by = lerp(hands.L.y - 12 * ms, (hands.L.y + hands.R.y) / 2 - 10 * ms, toChest);
  bowlSide(bx, by, 40, tilt, fill);
  circle(hands.L.x, hands.L.y, 8.5 * ms, C.skin); circle(hands.R.x, hands.R.y, 8.5 * ms, C.skin);
  if (t < 15.6) drawDaughter();
  for (const [k, hx, k0] of [[kissF, 152, 11.95], [kissM, 375, 13.7]]) { // a little heart rises from each kiss
    if (k <= 0) continue;
    const hy = 345 - seg(t, k0, k0 + .5) * 40, sz = 9;
    ctx.beginPath(); ctx.moveTo(hx, hy + sz);
    ctx.bezierCurveTo(hx - sz * 2, hy - sz * .5, hx - sz * .8, hy - sz * 1.8, hx, hy - sz * .6);
    ctx.bezierCurveTo(hx + sz * .8, hy - sz * 1.8, hx + sz * 2, hy - sz * .5, hx, hy + sz);
    ctx.fillStyle = `rgba(230,90,120,${k})`; ctx.fill();
  }

  // water droplets in slow motion, then shimmering wet spots on the road
  const Rn = rng(42), N = 110;
  for (let i = 0; i < N; i++) {
    const te = 17.82 + .4 * i / N, vx = 280 + Rn() * 340, vy = -260 + Rn() * 200, groundY = 560 + Rn() * 140, r = 2 + Rn() * 3.6;
    const ox = 480 + Rn() * 14, oy = 410 + Rn() * 10, tau = t - te, gr = 620;
    if (tau < 0) continue;
    const tLand = (-vy + Math.sqrt(vy * vy + 2 * gr * (groundY - oy))) / gr;
    if (tau < tLand) {
      const px = ox + vx * tau, py = oy + vy * tau + .5 * gr * tau * tau;
      circle(px, py, r, 'rgba(150,215,240,.9)'); circle(px - r * .35, py - r * .35, r * .35, 'rgba(255,255,255,.95)');
    } else {
      const lx = ox + vx * tLand, age = tau - tLand;
      const wet = .7 * (1 - age / 1.6);
      if (i % 3 || wet <= 0) continue;
      ellipse(lx, groundY, r * 4 * Math.min(1, age * 4 + .4), r * 1.1, `rgba(32,36,44,${wet * .55})`);
      if ((i + Math.floor(t * 8)) % 4 === 0) star8(lx, groundY - 3, 5, `rgba(255,255,255,${Math.min(1, wet * 1.6)})`);
    }
  }

  // closing title
  const ta = seg(t, 18.8, 19.5);
  persianBorder(ta);
  if (ta > 0) {
    ctx.save(); ctx.globalAlpha = ta * .85;
    rr(370, 52, 540, 156, 24); ctx.fillStyle = C.cream; ctx.fill();
    ctx.strokeStyle = C.gold; ctx.lineWidth = 3; rr(380, 62, 520, 136, 18); ctx.stroke();
    ctx.globalAlpha = ta; ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(255,255,255,.9)'; ctx.shadowBlur = 16;
    ctx.fillStyle = C.blueDark; ctx.font = '700 84px Vazirmatn, Tahoma, sans-serif'; ctx.fillText('سفر بخیر', 640, 140);
    ctx.font = '400 26px "Segoe UI", Tahoma, sans-serif'; ctx.fillText('Safar bekheyr — have a safe journey', 640, 186);
    ctx.restore();
  }
}
function carRear(cx, cy, sc, t, inside, waving) {
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc);
  ellipse(0, 2, 132, 14, 'rgba(0,0,0,.25)');
  ctx.fillStyle = '#222'; rr(-112, -24, 36, 28, 6); ctx.fill(); rr(76, -24, 36, 28, 6); ctx.fill();
  rr(-120, -112, 240, 96, 18); ctx.fillStyle = '#eceae6'; ctx.fill();
  ctx.beginPath(); ctx.moveTo(-92, -110); ctx.lineTo(-70, -176); ctx.quadraticCurveTo(0, -186, 70, -176); ctx.lineTo(92, -110); ctx.closePath(); ctx.fillStyle = '#e2dfda'; ctx.fill();
  ctx.beginPath(); ctx.moveTo(-80, -116); ctx.lineTo(-62, -166); ctx.quadraticCurveTo(0, -174, 62, -166); ctx.lineTo(80, -116); ctx.closePath(); ctx.fillStyle = '#3b4a5a'; ctx.fill();
  if (inside) { circle(-28, -138, 15, '#24303b'); ellipse(-28, -118, 22, 10, '#24303b'); }  // daughter inside
  if (waving > 0) {                                                                         // her waving hand
    ctx.save(); ctx.translate(-2, -122 - 10 * waving); ctx.rotate(Math.sin(t * 9) * .35);
    ellipse(0, -14, 6, 12, C.skinDark); ctx.restore();
  }
  ctx.fillStyle = '#c8202c'; rr(-114, -98, 44, 18, 5); ctx.fill(); rr(70, -98, 44, 18, 5); ctx.fill();
  rr(-40, -72, 80, 22, 3); ctx.fillStyle = '#fff'; ctx.fill();
  ctx.fillStyle = '#1d4fa0'; ctx.fillRect(-40, -72, 12, 22); ctx.fillStyle = '#222'; ctx.fillRect(-20, -64, 52, 6);
  rr(-118, -36, 236, 14, 6); ctx.fillStyle = '#cfccc6'; ctx.fill();
  ctx.restore();
}

// ---------- timeline ----------
function draw(realT) {
  const t = scriptTime(realT);
  ctx.setTransform(S, 0, 0, S, 0, 0);
  ctx.clearRect(0, 0, W, H);
  if (t < 3) sceneSini(t);
  else if (t < 9.4) sceneHall(t);
  else if (t < 11.4) sceneKiss(t);
  else if (t < 11.4 + HB) sceneHallOut(t - 11.4);
  else sceneStreet(t - HB);
  let a = t < .5 ? 1 - t / .5 : 0;
  for (const b of [3, 9.4, 11.4, 11.4 + HB]) a = Math.max(a, 1 - Math.abs(t - b) / .28);
  if (a > 0) { ctx.fillStyle = `rgba(246,234,215,${clamp(a)})`; ctx.fillRect(0, 0, W, H); }
  const g = ctx.createRadialGradient(640, 360, 320, 640, 360, 820);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.28)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

// ---------- music: an original piece in dastgah-e Shur, synthesised with Web Audio ----------
// Shur on D, with its half-flat second (koron, ~150 cents): D E-koron F G A Bb C
const SHUR = [0, 150, 300, 500, 700, 800, 1000];
const deg = n => 146.83 * Math.pow(2, Math.floor(n / 7) + SHUR[((n % 7) + 7) % 7] / 1200); // 0 = D3, 7 = D4, 14 = D5
// script time -> real seconds (inverse of scriptTime), so the music follows the scenes
const realTime = sTime => SLOW.reduce((r, [a, b, k]) => sTime > a ? r + (Math.min(sTime, b) - a) * (1 / k - 1) : r, sTime);

function makeMusic(ac, out, t0) {
  const noise = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
  { const d = noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
  const ir = ac.createBuffer(2, ac.sampleRate * 2.6, ac.sampleRate);           // soft hall reverb
  for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3); }
  const bus = ac.createGain(), rev = ac.createConvolver(), wet = ac.createGain();
  rev.buffer = ir; wet.gain.value = .32; bus.gain.value = 1.7;
  bus.connect(out); bus.connect(rev); rev.connect(wet); wet.connect(out);
  const T = r => t0 + r;
  const env = (g, at, peak, attack, release, hold = 0) => {
    g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(peak, at + attack);
    if (hold) g.gain.setValueAtTime(peak, at + attack + hold);
    g.gain.exponentialRampToValueAtTime(.0005, at + attack + hold + release);
  };
  const noiseSrc = (at, dur) => { const n = ac.createBufferSource(); n.buffer = noise; n.loop = true; n.start(at); n.stop(at + dur); return n; };

  // santur: a course of slightly detuned hammered strings with a bright, fast-decaying attack
  function santur(r, n, vel = .5, dur = 2.4) {
    const at = T(r), f = deg(n), g = ac.createGain(), lp = ac.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.setValueAtTime(5200, at); lp.frequency.exponentialRampToValueAtTime(1400, at + .5);
    g.connect(lp); lp.connect(bus); env(g, at, vel * .11, .003, dur);
    for (const [mult, type, det, lvl] of [[1, 'triangle', -4, 1], [1, 'triangle', 4, 1], [2.003, 'sine', 0, .45], [3.01, 'sine', 0, .18]]) {
      const o = ac.createOscillator(), og = ac.createGain();
      o.type = type; o.frequency.value = f * mult; o.detune.value = det; og.gain.value = lvl;
      o.connect(og); og.connect(g); o.start(at); o.stop(at + dur + .1);
    }
  }
  const riz = (r, n, len, vel = .35) => { for (let k = 0; k * .075 < len; k++) santur(r + k * .075, n, vel * (.7 + .3 * Math.sin(k)), .5); };

  // ney: breathy flute with a gentle vibrato
  function ney(r, n, dur, vel = .5) {
    const at = T(r), f = deg(n), g = ac.createGain(); g.connect(bus);
    g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(vel * .09, at + .28);
    g.gain.setValueAtTime(vel * .09, at + Math.max(.3, dur - .3)); g.gain.linearRampToValueAtTime(0, at + dur + .35);
    const o = ac.createOscillator(), o2 = ac.createOscillator(), g2 = ac.createGain(), lfo = ac.createOscillator(), lg = ac.createGain();
    o.frequency.value = f; o2.type = 'triangle'; o2.frequency.value = f * 2; g2.gain.value = .12;
    lfo.frequency.value = 5.2; lg.gain.value = f * .005; lfo.connect(lg); lg.connect(o.frequency); lg.connect(o2.frequency);
    o.connect(g); o2.connect(g2); g2.connect(g);
    const bp = ac.createBiquadFilter(), bg = ac.createGain(); bp.type = 'bandpass'; bp.frequency.value = f * 2; bp.Q.value = 1.2; bg.gain.value = .35;
    noiseSrc(at, dur + .5).connect(bp); bp.connect(bg); bg.connect(g);
    for (const x of [o, o2, lfo]) { x.start(at); x.stop(at + dur + .5); }
  }
  // low drone on D and A
  function drone(r0, r1, vel = .5) {
    const g = ac.createGain(); g.connect(bus);
    g.gain.setValueAtTime(0, T(r0)); g.gain.linearRampToValueAtTime(vel * .05, T(r0) + 1.5);
    g.gain.setValueAtTime(vel * .05, T(r1) - 1.5); g.gain.linearRampToValueAtTime(0, T(r1));
    for (const n of [-7, -3, 0]) { const o = ac.createOscillator(); o.frequency.value = deg(n); o.connect(g); o.start(T(r0)); o.stop(T(r1) + .1); }
  }
  // daf: deep "dom" or bright "tak"
  function daf(r, low, vel = .5) {
    const at = T(r), g = ac.createGain(); g.connect(bus);
    if (low) {
      const o = ac.createOscillator(), og = ac.createGain();
      o.frequency.setValueAtTime(110, at); o.frequency.exponentialRampToValueAtTime(52, at + .3);
      o.connect(og); og.connect(g); env(og, at, vel * .55, .004, .4); o.start(at); o.stop(at + .5);
    }
    const bp = ac.createBiquadFilter(), ng = ac.createGain(); bp.type = 'bandpass'; bp.frequency.value = low ? 380 : 2600; bp.Q.value = .9;
    noiseSrc(at, .3).connect(bp); bp.connect(ng); ng.connect(g); env(ng, at, vel * (low ? .25 : .3), .002, low ? .2 : .09);
  }
  // water thrown onto the street
  function splash(r) {
    const at = T(r), bp = ac.createBiquadFilter(), g = ac.createGain();
    bp.type = 'bandpass'; bp.Q.value = .8; bp.frequency.setValueAtTime(2400, at); bp.frequency.exponentialRampToValueAtTime(600, at + 1.1);
    noiseSrc(at, 1.6).connect(bp); bp.connect(g); g.connect(bus); env(g, at, .32, .03, 1.3);
    for (let k = 0; k < 14; k++) { // droplets landing
      const dt = .35 + Math.random() * 1.1, f2 = ac.createBiquadFilter(), g2 = ac.createGain();
      f2.type = 'bandpass'; f2.frequency.value = 2500 + Math.random() * 3000; f2.Q.value = 6;
      noiseSrc(at + dt, .1).connect(f2); f2.connect(g2); g2.connect(bus); env(g2, at + dt, .12, .002, .06);
    }
  }

  // ---- the score, placed on the real-time positions of the scenes ----
  const passEnd = k => realTime(3.7 + 5.3 * k / 3);
  const kissAt = realTime(9.4), outAt = realTime(11.4), streetAt = realTime(11.4 + HB);
  const waterAt = realTime(17.82 + HB), endAt = DUR;

  // 1. the sini: a slow opening arpeggio
  santur(.2, 0, .55, 3); santur(.2, 7, .45, 3);
  [[.8, 9], [1.2, 11], [1.6, 10], [2.0, 9], [2.3, 8]].forEach(([r, n]) => santur(r, n, .45));
  riz(2.6, 7, .5);
  drone(2.6, kissAt + .6, .9);

  // 2. passing under the Qur'an: one phrase per pass, each ending with a soft chime
  const phrases = [[7, 8, 9, 10, 9, 8, 9], [9, 10, 11, 12, 11, 10, 11], [11, 12, 13, 12, 11, 9, 8]];
  phrases.forEach((ph, k) => {
    const r0 = passEnd(k), len = passEnd(k + 1) - r0, st = len / 8;
    santur(r0, k === 2 ? -3 : 0, .5, 3); santur(r0 + len / 2, -3, .35, 2.5);
    ph.forEach((n, i) => santur(r0 + .15 + i * st, n, .42 + (i === 3 ? .1 : 0)));
    santur(r0 + len, 14, .5, 3); santur(r0 + len, 11, .35, 3);         // the chime at the end of the pass
  });
  ney(passEnd(2) - .2, 7, kissAt - passEnd(2) + .6, .6);

  // 3. the kiss: a tender ney phrase over sparse santur
  ney(kissAt + .15, 11, .9, .8); ney(kissAt + 1.05, 10, .45, .7); ney(kissAt + 1.5, 9, .5, .7); ney(kissAt + 2.0, 8, .9, .7);
  santur(kissAt + .15, 4, .35, 3); santur(kissAt + 1.05, 2, .3, 3);

  // 4. walking out of the house: the daf comes in under a running santur line
  const e8 = .3, walkLine = [7, 9, 11, 9, 10, 8, 9, 7];
  for (let i = 0; outAt + i * e8 < streetAt + 2.6; i++) {
    const r = outAt + i * e8, bar = i % 6;
    if (bar === 0) daf(r, true, .55); else if (bar === 3) daf(r, true, .35); else if (bar === 2 || bar === 5) daf(r, false, .35);
    if (r < streetAt) santur(r + .02, walkLine[i % 8], .36, 1.4);
  }
  santur(outAt, 0, .45, 3); santur(outAt + 1.8, -3, .4, 3);
  drone(outAt, waterAt + .5, .7);

  // 5. the goodbyes on the street: the emotional high point, ney doubling the santur
  const sb = streetAt + .05, line = [[0, 14, 1.2], [1.2, 13, .4], [1.6, 12, .4], [2.0, 11, 1.2], [3.2, 12, .4], [3.6, 11, .4],
    [4.0, 10, .4], [4.4, 9, 1.0], [5.4, 10, .4], [5.8, 11, .4], [6.2, 12, .4], [6.6, 11, .9]];
  for (const [o, n, d] of line) { if (sb + o > waterAt - .2) break; santur(sb + o, n, .48); if (d >= .9) ney(sb + o, n, d, .55); }
  [[0, 0], [2.0, -2], [4.0, -4], [6.0, -3]].forEach(([o, n]) => { if (sb + o < waterAt) santur(sb + o, n, .45, 3.2); });

  // 6. the water: a splash, a bright upward run and a long tremolo, then the closing cadence
  splash(waterAt);
  for (let k = 0; k <= 7; k++) santur(waterAt + .05 + k * .055, 7 + k, .4, 1.6);
  riz(waterAt + .5, 14, .9, .4);
  santur(waterAt + 1.5, 8, .45, 2); riz(waterAt + 1.9, 7, 1.0, .38);
  santur(waterAt + 1.9, 0, .5, 3.5); santur(waterAt + 1.9, -7, .4, 3.5);
  ney(waterAt + 1.6, 7, endAt - waterAt - 1.9, .5);
  out.gain.setValueAtTime(1, T(endAt - 1.2)); out.gain.linearRampToValueAtTime(0, T(endAt + .2));
}


window.SAFAR = { cv, draw, DUR, makeMusic };
})();
