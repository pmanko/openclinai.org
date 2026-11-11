/* openclinai dashboard shell (v2 — 100% pure JSON + pooled records/sources + live :8099 support) */
(function () {
  var cls = function (s) {
    return { done: 'c200', err: 'cerr', running: 'crun', pending: 'cpend' }[s] || 'cpend';
  };
  var sym = function (s) {
    return { done: '\u2713', err: '\u00d7', running: '\u25cf', pending: '\u00b7' }[s] || '\u00b7';
  };

  var ARM_CARDS = {};
  var ARM_LABELS = {};
  var EDITORIAL = null;
  var LAST_STATUS = null;
  var STATIC_DASHBOARD = null;

  function loadEditorial() {
    if (EDITORIAL !== null) return EDITORIAL;
    var el = document.getElementById('report-editorial');
    if (el && el.textContent && el.textContent.trim()) {
      try {
        EDITORIAL = JSON.parse(el.textContent);
        return EDITORIAL;
      } catch (e) {}
    }
    EDITORIAL = {};
    return EDITORIAL;
  }

  function armEditorialFor(b) {
    var ed = loadEditorial();
    var map = (ed && ed.arm_labels) || {};
    var v = map[b];
    if (!v) return {};
    if (typeof v === 'string') return { label: v, short: v };
    return v;
  }

  var armTitle = function (b) {
    var eo = armEditorialFor(b);
    if (eo.label) return eo.label;
    var c = ARM_CARDS[b];
    return (c && c.title) || ARM_LABELS[b] || b;
  };
  var armShort = function (b) {
    var eo = armEditorialFor(b);
    if (eo.short || eo.label) return eo.short || eo.label;
    var c = ARM_CARDS[b];
    return (c && (c.short_title || c.title)) || ARM_LABELS[b] || b;
  };
  var shortB = function (b) {
    return armShort(b);
  };

  var esc = function (s) {
    return (s == null ? '' : String(s))
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  };
  var TONE_CLS = { success: 't-ok', warning: 't-warn', danger: 't-bad', neutral: 't-neutral' };
  var toneCls = function (t) {
    return TONE_CLS[t] || 't-neutral';
  };
  var fmtS = function (ms) {
    return ms == null || isNaN(ms) ? 'n/a' : (Number(ms) / 1000).toFixed(1) + ' s';
  };
  var fmt10 = function (v, na) {
    if (na === undefined) na = '\u2014';
    if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) return na;
    var n = Number(v);
    var r = Math.round(n * 10) / 10;
    return Number.isInteger(r) ? String(Math.trunc(r)) : r.toFixed(1);
  };

  function inlineMarkdown(escapedText) {
    var text = String(escapedText == null ? '' : escapedText);
    text = text.replace(
      /\*\((Check:[^)]*)\)\*/g,
      '<em class="claim-mark">($1)</em>'
    );
    text = text.replace(
      /\*\((General guidance[^)]*)\)\*/g,
      '<em class="claim-guidance">($1)</em>'
    );
    text = text.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    text = text.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');
    return text;
  }

  function renderMarkdown(rawText) {
    var body = String(rawText == null ? '' : rawText).trim();
    if (!body) return '';
    var lines = body.split(/\r?\n/);
    var items = [];
    var paragraphs = [];
    lines.forEach(function (raw) {
      var stripped = raw.trim();
      if (!stripped) return;
      if (stripped.indexOf('- ') === 0 || stripped.indexOf('* ') === 0) {
        items.push('<li>' + inlineMarkdown(esc(stripped.slice(2).trim())) + '</li>');
      } else {
        paragraphs.push('<p class="md-p">' + inlineMarkdown(esc(stripped)) + '</p>');
      }
    });
    if (items.length && !paragraphs.length) {
      return '<ul class="md-list">' + items.join('') + '</ul>';
    }
    if (items.length) {
      return paragraphs.join('') + '<ul class="md-list">' + items.join('') + '</ul>';
    }
    return paragraphs.join('');
  }

  var CHECKPREC_ANSWER_CHECKS = ['date', 'date_patched', 'record', 'citation', 'review', 'needs_review'];
  var CHECKPREC_INDEPTH_CHECKS = ['date', 'citation', 'review', 'marked'];
  var CHECKPREC_LABELS = {
    date: 'Date check',
    date_patched: 'Date check (answer patched; judged after the patch)',
    record: 'Record check',
    citation: 'Citation support',
    review: 'Model review',
    needs_review: 'Status: needs review',
    marked: 'Any mark'
  };
  var CHECKPREC_VERDICTS = ['correct', 'wrong_fact', 'wrong_citation', 'unsupported', 'guidance'];
  var CHECKPREC_EXPLANATION = 'Precision: of the items a check marked, the share the judge also faulted. Recall: of the items the judge faulted, the share the check marked.';

  function fmtCheckPrecRatio(v) {
    return v == null || isNaN(v) ? 'n/a' : Number(v).toFixed(2);
  }
  function renderCheckPrecTableHtml(head, rows, caption) {
    var h = "<table class='summary checkprec'><caption>" + esc(caption) + '</caption><thead><tr>';
    h += head.map(function (c) { return '<th>' + esc(c) + '</th>'; }).join('') + '</tr></thead><tbody>';
    rows.forEach(function (row) {
      h += '<tr>' + row.map(function (c, i) {
        return (i === 0 ? "<td class='b'>" : '<td>') + esc(c) + '</td>';
      }).join('') + '</tr>';
    });
    return h + '</tbody></table>';
  }
  function buildCheckPrecisionHtml(data) {
    if (!data || typeof data !== 'object' || (!data.answer && !data.indepth)) return '';
    var ref = data.reference || {};
    var actors = ref.actors || [];
    var otherActors = actors.filter(function (a) { return a !== ref.headline; });
    var h =
      "<div class='checkprec'><p class='intro'>" + esc(CHECKPREC_EXPLANATION) +
      ' Reference: the ' + esc(String(ref.headline || 'judge')) + ' judge pass' +
      ' (an accuracy below ' + esc(String((ref.thresholds || {}).accuracy_error_below)) + ',' +
      ' a citation the judge found unsupported or partly supported, harm, or a temporal axis not ok counts as a judged error).' +
      (otherActors.length ? ' Other passes scored: ' + esc(otherActors.join(', ')) + '.' : '') +
      '</p>';
    var ansHead = ['check', 'marked', 'marked, any turn', 'judged errors', 'hits', 'precision', 'recall'];
    var idHead = ['check', 'marked', 'judged errors', 'hits', 'precision', 'recall'];
    function ansRows(block) {
      return CHECKPREC_ANSWER_CHECKS.map(function (chk) {
        var s = (block && block[chk]) || {};
        return [
          CHECKPREC_LABELS[chk] || chk,
          String(s.marked || 0),
          String(s.marked_any_turn || 0),
          String(s.judged_errors || 0),
          String(s.hits || 0),
          fmtCheckPrecRatio(s.precision),
          fmtCheckPrecRatio(s.recall)
        ];
      });
    }
    function idRows(block) {
      return CHECKPREC_INDEPTH_CHECKS.map(function (chk) {
        var s = (block && block[chk]) || {};
        return [
          CHECKPREC_LABELS[chk] || chk,
          String(s.marked || 0),
          String(s.judged_errors || 0),
          String(s.hits || 0),
          fmtCheckPrecRatio(s.precision),
          fmtCheckPrecRatio(s.recall)
        ];
      });
    }
    var answer = data.answer || {};
    var ansExtra = [];
    if (answer.unmatched_cells) ansExtra.push(answer.unmatched_cells + ' unmatched');
    if (answer.unscored_rows) ansExtra.push(answer.unscored_rows + ' unscored');
    var ansCaption = 'Answer checks, all arms (' + (answer.cells || 0) + ' judged cells' + (ansExtra.length ? ', ' + ansExtra.join(', ') : '') + ')';
    h += renderCheckPrecTableHtml(ansHead, ansRows(answer.overall || {}), ansCaption);
    var byArm = answer.by_arm || {};
    var armKeys = Object.keys(byArm);
    if (armKeys.length) {
      h += "<details class='checkprec-arms' data-okey='checkprec:ans-by-arm'><summary>Answer checks per arm</summary>";
      armKeys.forEach(function (arm) {
        var blk = byArm[arm] || {};
        var n = ((blk.needs_review || {}).n) || 0;
        h += renderCheckPrecTableHtml(ansHead, ansRows(blk), armTitle(arm) + ' (' + n + ' cells)');
      });
      h += '</details>';
    }
    var indepth = data.indepth || {};
    if (!indepth.available) {
      var mObj = indepth.marked || {};
      var marks = Object.keys(mObj).map(function (c) { return (CHECKPREC_LABELS[c] || c) + ' ' + mObj[c]; }).join(', ');
      h += "<p class='intro'>In-Depth per point: no per-point verdicts in the judge rows (" + (indepth.points || 0) + ' points; marks: ' + esc(marks) + ').</p>';
    } else {
      var idCaption =
        'In-Depth checks per point, all arms (' + (indepth.judged_points || 0) + ' judged of ' + (indepth.points || 0) + ' points' +
        (indepth.unmatched_verdicts ? ', ' + indepth.unmatched_verdicts + ' unmatched verdicts' : '') + ')';
      h += renderCheckPrecTableHtml(idHead, idRows(indepth.overall || {}), idCaption);
      var vHead = ['check']
        .concat(CHECKPREC_VERDICTS.map(function (v) { return 'marked: ' + v; }))
        .concat(CHECKPREC_VERDICTS.map(function (v) { return 'unmarked: ' + v; }));
      var vRows = CHECKPREC_INDEPTH_CHECKS.map(function (chk) {
        var by = (((indepth.overall || {})[chk] || {}).by_verdict) || {};
        return [CHECKPREC_LABELS[chk] || chk]
          .concat(CHECKPREC_VERDICTS.map(function (v) { return String((by.marked || {})[v] || 0); }))
          .concat(CHECKPREC_VERDICTS.map(function (v) { return String((by.unmarked || {})[v] || 0); }));
      });
      h += renderCheckPrecTableHtml(vHead, vRows, 'Marks by judge verdict, all arms');
      var idArms = indepth.by_arm || {};
      var idArmKeys = Object.keys(idArms);
      if (idArmKeys.length) {
        h += "<details class='checkprec-arms' data-okey='checkprec:id-by-arm'><summary>In-Depth checks per arm</summary>";
        idArmKeys.forEach(function (arm) {
          var blk = idArms[arm] || {};
          var n = ((blk.marked || {}).n) || 0;
          h += renderCheckPrecTableHtml(idHead, idRows(blk), armTitle(arm) + ' (' + n + ' judged points)');
        });
        h += '</details>';
      }
    }
    return h + '</div>';
  }

  var KNOB_ORDER = ['temp', 'top_p', 'top_k', 'ctx_size', 'seed', 'max_tokens', 'reasoning_budget', 'dry'];
  var KNOB_LABELS = {
    temp: 'temperature',
    top_p: 'top-p',
    top_k: 'top-k',
    ctx_size: 'ctx-size',
    seed: 'seed',
    max_tokens: 'max-tokens',
    reasoning_budget: 'reasoning-budget',
    dry: 'DRY'
  };

  function renderArmConfig(cfg, key) {
    if (!cfg) return '';
    var knobs = cfg.knobs || {};
    var models = Object.keys(knobs);
    var k0 = (models.length ? knobs[models[0]] : {}) || {};
    var tease = [];
    if (k0.temp != null) tease.push('temp ' + k0.temp);
    if (k0.seed != null) tease.push('seed ' + k0.seed);
    if (k0.dry != null) tease.push('DRY on');
    if (k0.ctx_size != null) tease.push('ctx ' + k0.ctx_size);
    var np = (cfg.prompts || []).length;
    if (np) tease.push(np + ' system prompt' + (np > 1 ? 's' : ''));
    var teaseTxt = tease.length ? ' \u2014 ' + tease.join(' \u00b7 ') : '';
    var h =
      "<details class=arm-config data-okey='cfg:" + esc(key) + "'><summary>how this arm is configured<span class=ac-tease>" +
      esc(teaseTxt) +
      '</span></summary><div class=ac-body>';
    if (models.length) {
      var present = KNOB_ORDER.filter(function (k) {
        return models.some(function (m) {
          return (knobs[m] || {})[k] != null;
        });
      });
      h += '<div class=ac-h>sampling knobs <span class=ac-sub>(llama-router.ini)</span></div>';
      h += '<table class=ac-knobs><thead><tr><th>knob</th>';
      models.forEach(function (m) {
        h += '<th>' + esc(m) + '</th>';
      });
      h += '</tr></thead><tbody>';
      present.forEach(function (k) {
        h += '<tr><td class=ac-k>' + esc(KNOB_LABELS[k] || k) + '</td>';
        models.forEach(function (m) {
          var v = (knobs[m] || {})[k];
          h += '<td>' + (v == null ? '\u2014' : esc(v)) + '</td>';
        });
        h += '</tr>';
      });
      h += '</tbody></table>';
    }
    var prompts = cfg.prompts || [];
    if (prompts.length) {
      h += '<div class=ac-h>system prompt' + (prompts.length > 1 ? 's' : '') + '</div>';
      prompts.forEach(function (p, i) {
        h += '<div class=ac-prompt>';
        h += '<div class=ac-plabel>' + esc(p.label) + ' <span class=ac-src>' + esc(p.source) + '</span></div>';
        if (p.summary) h += '<div class=ac-psum>' + esc(p.summary) + '</div>';
        h +=
          "<details class=ac-pfull data-okey='prompt:" + esc(key) + ':' + i + "'><summary>full prompt</summary><pre class=ac-pre>" +
          esc(p.text) +
          '</pre></details>';
        h += '</div>';
      });
    }
    var r = cfg.retrieval;
    if (r) {
      h += '<div class=ac-h>retrieval <span class=ac-sub>(chartsearchai GPs)</span></div>';
      h +=
        '<div class=ac-retr>pipeline ' + esc(r.pipeline) +
        ' \u00b7 embedding top-k ' + esc(r.embedding_topk) +
        ' \u00b7 querystore top-k ' + esc(r.querystore_topk) +
        ' \u00b7 threshold ' + esc(r.threshold) + '</div>';
    }
    h += '</div></details>';
    return h;
  }

  function renderArmCards(d) {
    var cards = d.arm_cards || {};
    var stats = d.arms || {};
    var h = '<div class=arm-cards>';
    (d.backends || []).forEach(function (b) {
      var c = cards[b] || { kind: 'unknown', path: '', models: [], roles: {} };
      var a = stats[b] || {};
      var team = c.kind === 'team';
      var badge = team
        ? "<span class='badge team'>TEAM</span>"
        : c.kind === 'single'
        ? "<span class='badge single'>SINGLE</span>"
        : '<span class=badge>?</span>';
      var eo = armEditorialFor(b);
      var title = eo.label || c.title || a.label || b;
      h += '<div class=arm-card>';
      h += '<div class=arm-head>' + badge + '<span class=arm-name>' + esc(title) + '</span></div>';
      h += '<div class=arm-id>' + esc(b) + '</div>';
      var pt = (d.profile_titles || {})[b];
      if (pt && pt !== title) h += '<div class=arm-profile>product profile: ' + esc(pt) + '</div>';
      if (c.path) h += '<div class=arm-path>' + esc(c.path) + '</div>';
      h +=
        '<div class=arm-stats>' + (a.rows || 0) + " rows \u00b7 <span class='" + (a.errors ? 'err' : 'ok') + "'>" +
        (a.errors || 0) + ' err</span> \u00b7 <span class=muted>avg ' + fmtS(a.avg_latency_ms || 0) +
        ' \u00b7 ' + (a.avg_chars || 0) + 'c' + (a.last ? ' \u00b7 ' + esc(a.last) : '') + '</span></div>';
      if (team) {
        h += '<table class=makeup><tbody>';
        Object.keys(c.roles || {}).forEach(function (role) {
          var m = c.roles[role] || {};
          var mq = [m.family, m.params, m.quant].filter(Boolean).join(' \u00b7 ');
          h += '<tr><td class=role>' + esc(role) + '</td><td class=mq>' + esc(mq) + '</td></tr>';
        });
        h += '</tbody></table>';
      } else {
        var m = (c.models || [])[0] || {};
        var mq = [m.family, m.params, m.quant].filter(Boolean).join(' \u00b7 ');
        h += '<div class=makeup-single>' + esc(mq) + '</div>';
      }
      h += renderArmConfig(c.config, b);
      h += '</div>';
    });
    return h + '</div>';
  }

  function renderJudgeScores(d) {
    var rows = (d.judge_combined || [])
      .filter(function (s) {
        return (s.n_actors || 0) >= 1 && s.benchmark_score != null;
      })
      .sort(function (a, b) {
        return (b.benchmark_score || 0) - (a.benchmark_score || 0);
      });
    if (!rows.length) return '<span class=muted>no judged score yet</span>';
    var judging = d.judging || {};
    var actors =
      judging.recorded || (judging.cards && judging.cards.length)
        ? judging.sentence
        : 'Judge not recorded for this run. Actors: ' + (d.judge_actors || []).join(', ');
    var multi = rows.some(function (s) {
      return (s.n_actors || 0) > 1;
    });
    var canon = {};
    (d.judge || []).forEach(function (s) {
      if (s && s.benchmark_score != null) canon[s.backend] = s.benchmark_score;
    });
    var hasCanon = Object.keys(canon).length > 0;
    var note = multi
      ? hasCanon
        ? 'Canonical score = the headline above. Combined = each cell averaged across independent judges, then averaged per arm. Range and max \u0394 show judge disagreement.'
        : 'Combined = each cell averaged across independent judges, then averaged per arm. Range and max \u0394 show judge disagreement.'
      : 'Score from one independent judge. Add another judge to show disagreement ranges.';
    var h = '<p class=judge-note>' + esc(actors) + ' ' + note + '</p>';
    h +=
      '<table class=judge-table><thead><tr><th>setup</th><th>' +
      (hasCanon ? 'canonical score' : 'score') + '</th>' +
      (multi && hasCanon ? '<th>mean across actors</th>' : '') +
      '<th>actors</th><th>cell range</th><th>actor range</th><th>mean \u0394/cell</th><th>max \u0394 cell</th></tr></thead><tbody>';
    rows.forEach(function (s) {
      var ar = s.actor_range || {},
        sp = s.benchmark_spread || {};
      var maxCell = s.max_cell_delta_scenario ? esc(s.max_cell_delta_scenario) + ' \u00b7 ' + fmt10(s.max_cell_delta) : '\u2014';
      var primary = hasCanon && canon[s.backend] != null ? canon[s.backend] : s.benchmark_score;
      h +=
        '<tr><td title="' + esc(s.backend) + '">' + esc(armTitle(s.backend)) + '</td>' +
        '<td><span class=score>' + fmt10(primary) + '</span></td>' +
        (multi && hasCanon ? '<td>' + fmt10(s.benchmark_score) + '</td>' : '') +
        '<td>' + (s.n_actors || 0) + '</td>' +
        '<td>' + (sp.min == null ? '\u2014' : fmt10(sp.min) + '\u2013' + fmt10(sp.max)) + '</td>' +
        '<td>' + (ar.min == null ? '\u2014' : fmt10(ar.min) + '\u2013' + fmt10(ar.max)) + '</td>' +
        '<td>' + fmt10(s.mean_abs_delta) + '</td><td>' + maxCell + '</td></tr>';
    });
    var c = judging.consensus || {};
    if (c.alpha) {
      var th = c.thresholds || { acceptable: 0.667, good: 0.8 };
      h +=
        '<p class=judge-note>Agreement between the ' + (c.actors || []).length +
        ' passes (Krippendorff\u2019s alpha; ' + th.acceptable + ' acceptable, ' + th.good + ' good): ' +
        Object.keys(c.alpha)
          .map(function (k) {
            return esc(k) + ' ' + (c.alpha[k].alpha == null ? '\u2014' : c.alpha[k].alpha.toFixed(3)) + ' (' + esc(c.alpha[k].verdict) + ')';
          })
          .join(' \u00b7 ') + '</p>';
      var sp = (c.spread_cells || []).slice(0, 5);
      if (sp.length) {
        h +=
          '<p class=judge-note>Widest cells: ' +
          sp
            .map(function (s) {
              return esc(s.scenario_id) + ' \u00d7 ' + esc(armTitle(s.backend_id)) + ' range ' + fmt10(s.range);
            })
            .join(' \u00b7 ') + '</p>';
      }
      var j = c.judges || {};
      if (j.per_judge) {
        var jt = j.thresholds || { acceptable: 0.667, good: 0.8 };
        h +=
          '<p class=judge-note>Judges side by side (Benchmark per setup): ' +
          Object.keys(j.per_judge)
            .map(function (id) {
              return (
                esc(id) + ' [' +
                (j.per_judge[id].scout || [])
                  .map(function (s) {
                    return esc(armTitle(s.backend)) + ' ' + fmt10(s.benchmark_score);
                  })
                  .join(', ') + ']'
              );
            })
            .join(' \u00b7 ') +
          '. Agreement between judges (alpha; ' + jt.acceptable + ' acceptable, ' + jt.good + ' good): ' +
          Object.keys(j.alpha || {})
            .map(function (k) {
              return esc(k) + ' ' + (j.alpha[k].alpha == null ? '\u2014' : j.alpha[k].alpha.toFixed(3));
            })
            .join(' \u00b7 ') + '</p>';
      }
    }
    return h + '</tbody></table>';
  }

  var OPEN_DETAILS = new Set();
  document.addEventListener(
    'toggle',
    function (e) {
      var d = e.target;
      if (!d || d.tagName !== 'DETAILS') return;
      var k = d.getAttribute && d.getAttribute('data-okey');
      if (!k) return;
      if (d.open) OPEN_DETAILS.add(k);
      else OPEN_DETAILS.delete(k);
    },
    true
  );

  function restoreOpenDetails(root) {
    (root || document).querySelectorAll('details[data-okey]').forEach(function (d) {
      d.open = OPEN_DETAILS.has(d.getAttribute('data-okey'));
    });
  }

  function renderCheckPrecision(d) {
    var sec = document.getElementById('checksec'),
      box = document.getElementById('checkprec');
    if (!sec || !box) return;
    var html = buildCheckPrecisionHtml(d.check_precision);
    if (!html) {
      sec.style.display = 'none';
      box.innerHTML = '';
      box._rawHtml = '';
      return;
    }
    sec.style.display = '';
    if (box._rawHtml !== html) {
      box._rawHtml = html;
      box.innerHTML = html;
      restoreOpenDetails(box);
    }
  }

  function gridCell(g, oc) {
    var st = g.state;
    if (!g.answer && !g.indepth) return '<td class=' + cls(st) + oc + '>' + sym(st) + '</td>';
    var conform =
      {
        done: 'followed an allowed path',
        err: 'the system misbehaved',
        running: 'running',
        pending: 'pending'
      }[st] || '';
    var tip = [
      'Answer: ' + (g.answer ? g.answer.label : 'none'),
      'In-Depth: ' + (g.indepth ? g.indepth.label : 'none') + (g.marked ? ' (' + g.marked + ' marked point' + (g.marked > 1 ? 's' : '') + ')' : ''),
      conform
    ]
      .filter(Boolean)
      .join(' \u00b7 ');
    var pill = function (tag, v, n) {
      return v ? '<span class="gpill ' + toneCls(v.tone) + '">' + tag + ' ' + (n ? n + '' : '') + esc(v.symbol) + '</span>' : '';
    };
    var klass = st === 'done' ? 'cdone' : cls(st);
    return (
      '<td class=' + klass + oc + ' title="' + esc(tip) + '">' +
      pill('A', g.answer, 0) +
      pill('ID', g.indepth, g.marked) +
      '<span class="gconf' + (st === 'err' ? ' err' : '') + '">' + sym(st) + '</span></td>'
    );
  }

  function resolveSourcesList(sourcesObj) {
    if (!sourcesObj) return [];
    if (Array.isArray(sourcesObj.sources) && sourcesObj.sources.length) {
      return sourcesObj.sources;
    }
    var refs = sourcesObj.sources_pool_refs;
    var pool = (STATIC_DASHBOARD && STATIC_DASHBOARD.sources_pool) || [];
    if (Array.isArray(refs) && refs.length) {
      return refs.map(function (ref) {
        var pIdx = ref[0];
        var sid = ref[1];
        var cite = ref[2];
        var chart = ref[3];
        var recIdx = ref[4];
        var base = pool[pIdx] || {};
        return Object.assign({}, base, {
          source_id: sid != null ? sid : base.source_id,
          citation_index: cite != null ? cite : base.citation_index,
          chart_record_index: chart != null ? chart : base.chart_record_index,
          record_index: recIdx != null ? recIdx : (cite != null ? cite : base.record_index)
        });
      });
    }
    return [];
  }

  function resolveRefsList(turn) {
    if (!turn) return [];
    if (Array.isArray(turn.refs) && turn.refs.length) return turn.refs;
    if (turn.refs_pool_id != null && STATIC_DASHBOARD && Array.isArray(STATIC_DASHBOARD.refs_pool)) {
      return STATIC_DASHBOARD.refs_pool[turn.refs_pool_id] || [];
    }
    return [];
  }

  function srcLabels(sources) {
    var out = {};
    resolveSourcesList(sources).forEach(function (s) {
      if (s.record_index != null) out[s.record_index] = s.source_id;
    });
    return out;
  }

  function rowRefLabels(row, labels) {
    var seen = {},
      out = [];
    var cells = (row && row.cells) || {};
    Object.keys(cells).forEach(function (k) {
      ((cells[k] && cells[k].refs) || []).forEach(function (r) {
        var x = labels[r] || '[' + r + ']';
        if (!seen[x]) {
          seen[x] = 1;
          out.push(x);
        }
      });
    });
    return out;
  }

  function renderBlocks(blocks, sources) {
    if (!blocks || !blocks.length) return '';
    var labels = srcLabels(sources);
    return blocks
      .map(function (bl) {
        if (bl.kind !== 'table') return '';
        var cols = bl.columns || [];
        var head = cols
          .map(function (c) {
            return '<th>' + esc(c.label || c.key || '') + '</th>';
          })
          .join('');
        var body = (bl.rows || [])
          .map(function (row) {
            var cells = row.cells || {};
            var rr = rowRefLabels(row, labels);
            var rf = rr.length
              ? '<div class=rowrefs>sources ' +
                rr
                  .map(function (x) {
                    return '<span>' + esc(x) + '</span>';
                  })
                  .join('') +
                '</div>'
              : '';
            return (
              '<tr>' +
              cols
                .map(function (c, i) {
                  var cell = cells[c.key] || {};
                  var txt = esc(cell.text != null ? String(cell.text) : '');
                  return '<td>' + txt + (i === 0 ? rf : '') + '</td>';
                })
                .join('') +
              '</tr>'
            );
          })
          .join('');
        var title = bl.title ? '<div class=btitle>' + esc(bl.title) + '</div>' : '';
        return '<div class=block>' + title + '<table class=btbl><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>';
      })
      .join('');
  }

  function renderSources(sources) {
    var ss = resolveSourcesList(sources),
      d = (sources && sources.diagnostics) || {};
    if (!ss.length && !(d.malformed_tokens && d.malformed_tokens.length)) return '';
    function card(s) {
      var meta = [s.resource_type, s.date].filter(Boolean).map(esc).join(' \u00b7 ');
      var facts = (s.facts_used && s.facts_used.length ? s.facts_used : [s.source_text || s.title || '']).slice(0, 4);
      var cite = s.citation_index || s.record_index || '?';
      var chart = s.chart_record_index || s.record_index || '?';
      var tc = function (t) {
        return { success: 'ok', danger: 'bad', warning: 'warn' }[t] || '';
      };
      var secs = (s.sections || []).length
        ? s.sections
            .map(function (x) {
              return '<span class=ssec>' + esc(x) + '</span>';
            })
            .join('')
        : '<span class=sstat>not cited in the text</span>';
      return (
        '<div class=scard><div class=shead><b>' + esc(s.source_id || '') + '</b> cite [' + esc(cite) + '] \u00b7 chart [' + esc(chart) + '] ' + esc(s.title || '') + '</div>' +
        '<div class=smeta>cited by ' + secs + ' \u00b7 ' + meta +
        ' <span class="sstat ' + tc(s.record_tone) + '">' + esc(s.record_label || s.resolution_status || '') + '</span>' +
        ' <span class="sstat ' + tc(s.support_tone) + '">' + esc(s.support_label || s.support_status || '') + '</span></div>' +
        '<ul>' +
        facts
          .map(function (f) {
            return '<li>' + esc(f) + '</li>';
          })
          .join('') +
        '</ul>' +
        '<details><summary>open source record</summary><pre>' + esc(s.source_text || '') + '</pre></details></div>'
      );
    }
    var h = '<div class=sources><div class=stitle>Evidence Used</div><div class=sgrid>' + ss.slice(0, 5).map(card).join('') + '</div>';
    if (ss.length > 5) h += '<details><summary>show all sources</summary>' + ss.slice(5).map(card).join('') + '</details>';
    var bits = [];
    ['unresolved_refs', 'unused_top_refs', 'nested_only_refs', 'malformed_tokens'].forEach(function (k) {
      if (d[k] && d[k].length) bits.push(k + ': ' + JSON.stringify(d[k]));
    });
    if (bits.length) h += '<div class=sdiag>' + esc(bits.join(' \u00b7 ')) + '</div>';
    return h + '</div>';
  }

  function renderRawRefs(refs) {
    if (!refs || !refs.length) return '';
    return (
      '<details class=rawrefs><summary>raw resolved refs</summary><div>' +
      esc(
        refs
          .map(function (r) {
            return typeof r === 'object' ? '[' + (r.index != null ? r.index : '?') + '] ' + (r.resourceType || '') : '[' + r + ']';
          })
          .join('  ')
      ) +
      '</div></details>'
    );
  }

  function statusChip(v) {
    if (!v) return '';
    return (
      '<span class="schip ' + toneCls(v.tone) + '">' + esc(v.label || '') + '</span>' +
      (v.confidence ? '<span class=sconf>' + esc(v.confidence) + '</span>' : '')
    );
  }

  function findingsHtml(view) {
    var fs = (view && view.findings) || [];
    if (!fs.length) return '';
    return (
      '<ul class=findings>' +
      fs
        .map(function (f) {
          return (
            '<li class="' + toneCls(f.tone) + '"><b>' + esc(f.name || '') + '</b>' +
            (f.where ? ' <span class=fwhere>(' + esc(f.where) + ')</span>' : '') +
            (f.says ? ': ' + esc(f.says) : '') +
            '</li>'
          );
        })
        .join('') +
      '</ul>'
    );
  }

  function sectionHtml(title, view, bodyHtml, extra) {
    var h = '<div class=csec><div class=ctitle>' + title + ' ' + statusChip(view) + '</div>';
    if (view && view.note) h += '<div class="snote ' + toneCls(view.tone) + '">' + esc(view.note) + '</div>';
    h += findingsHtml(view);
    if (bodyHtml) h += '<div class=ans>' + bodyHtml + '</div>';
    return h + (extra || '') + '</div>';
  }

  function renderClaims(view) {
    var rows = (view && view.claims) || [];
    if (!rows.length) return '';
    var names = view.check_names || {};
    var cell = function (c) {
      if (!c) return '<td class="t-neutral">\u2014</td>';
      return '<td class="' + toneCls(c.tone) + '">' + esc(c.verdict) + (c.reason ? '<div class=creason>' + esc(c.reason) + '</div>' : '') + '</td>';
    };
    var h =
      '<table class=claims><thead><tr><th>#</th><th>point</th><th>cites</th>' +
      ['date', 'review', 'citation']
        .map(function (k) {
          return '<th>' + esc(names[k] || k) + '</th>';
        })
        .join('') +
      '</tr></thead><tbody>';
    rows.forEach(function (r) {
      var ch = r.checks || {};
      h +=
        '<tr' + (r.marked ? ' class=marked' : '') + '><td>' + r.index + '</td><td>' + esc(r.text) + '</td><td>' +
        ((r.cited || []).length
          ? r.cited
              .map(function (i) {
                return '[' + i + ']';
              })
              .join(' ')
          : '<span class=muted>none</span>') +
        '</td>' +
        cell(ch.date) +
        cell(ch.review) +
        cell(ch.citation) +
        '</tr>';
    });
    return h + '</tbody></table>';
  }

  function renderDraft(view, sourcesV1) {
    var d = view && view.draft;
    if (!d) return '';
    var sources = resolveSourcesList(sourcesV1);
    var rows = sources
      .map(function (s) {
        var idx = s.citation_index != null ? s.citation_index : s.record_index != null ? s.record_index : '?';
        var label = [s.date, s.resource_type, s.title].filter(Boolean).join(' \u00b7 ');
        var record = s.source_text ? '<details><summary>open draft source</summary><pre>' + esc(s.source_text) + '</pre></details>' : '';
        return '<li><b>[' + esc(String(idx)) + ']</b> ' + esc(label) + record + '</li>';
      })
      .join('');
    var src = rows ? '<div class=reviewrefs><b>Draft sources (not delivered evidence)</b><ul>' + rows + '</ul></div>' : '';
    return (
      '<details class=draftbox data-kind="' + esc(d.kind) + '"><summary>' + esc(d.title) + '</summary>' +
      '<div class=draftnote>' + esc(d.note) + '</div><div class=ans>' + esc(d.text) + '</div>' +
      src + '</details>'
    );
  }

  function renderRawCheck(view) {
    if (!view || !view.validation) return '';
    return (
      '<details class=rawrefs><summary>raw check record</summary><div><pre style="white-space:pre-wrap;margin:0">' +
      esc(JSON.stringify(view.validation, null, 1)) +
      '</pre></div></details>'
    );
  }

  function renderOriginalAnswer(validation) {
    if (!validation || !validation.originalAnswer) return '';
    var edited = validation.status === 'edited';
    var notice = edited
      ? 'This answer or its supporting citations was changed by the answer check. The checked answer above is the current result.'
      : 'This was the model output before checking. The current answer above remains flagged for review.';
    var sources = resolveSourcesList(validation.originalSources);
    var sourceRows = sources
      .map(function (s) {
        var idx = s.citation_index != null ? s.citation_index : s.record_index != null ? s.record_index : '?';
        var label = [s.date, s.resource_type, s.title].filter(Boolean).join(' \u00b7 ');
        var record = s.source_text ? '<details><summary>open original source</summary><pre>' + esc(s.source_text) + '</pre></details>' : '';
        return '<li><b>[' + esc(String(idx)) + ']</b> ' + esc(label) + record + '</li>';
      })
      .join('');
    var sourceHtml = sourceRows ? '<div class=reviewrefs><b>Original-answer sources (not final evidence)</b><ul>' + sourceRows + '</ul></div>' : '';
    return (
      '<details open class="reviewdraft' + (edited ? ' edited' : '') + '"><summary>Original model answer</summary>' +
      '<div class=reviewdraft-note>' + notice + '</div>' +
      '<div class=ans>' + esc(validation.originalAnswer) + renderBlocks(validation.originalBlocks || [], validation.originalSources || {}) + '</div>' +
      sourceHtml + '</details>'
    );
  }

  function resolveContextStepRecords(step) {
    var rPool = (STATIC_DASHBOARD && STATIC_DASHBOARD.record_pool) || [];
    var inc = step.included || [];
    if (!inc.length && Array.isArray(step.included_pool_ids)) {
      inc = step.included_pool_ids.map(function (id) {
        var p = rPool[id] || ['', ''];
        return { source_id: p[0], reason: p[1] };
      });
    }
    var exc = step.excluded || [];
    if (!exc.length && Array.isArray(step.excluded_pool_ids)) {
      exc = step.excluded_pool_ids.map(function (id) {
        var p = rPool[id] || ['', ''];
        return { source_id: p[0], reason: p[1] };
      });
    }
    return { included: inc, excluded: exc };
  }

  function renderTrace(tr) {
    if (!tr) {
      if (LAST_STATUS && LAST_STATUS.total && !LAST_STATUS.finished) {
        return '<div class=notrace>reasoning traces are joined when the run finishes</div>';
      }
      return '<div class=notrace>no reasoning trace captured for this turn (hub trace off, or older run)</div>';
    }
    var fmt = function (s) {
      if (s.role === 'context') {
        var recs = resolveContextStepRecords(s);
        var incCount = s.included_count != null ? s.included_count : recs.included.length;
        var excCount = s.excluded_count != null ? s.excluded_count : recs.excluded.length;
        var summary =
          (s.patient ? 'patient ' + esc(s.patient) + ' \u00b7 ' : '') +
          incCount + ' included / ' + (s.total_records || incCount + excCount) + ' total records (' + (s.chars || 0) + ' chars)';
        var incHtml = recs.included.length
          ? '<details class=collapse><summary>' + recs.included.length + ' included records</summary><ul class=idl>' +
            recs.included
              .map(function (r) {
                return '<li><b>' + esc(r.source_id || '') + '</b>' + (r.reason ? ' \u2014 ' + esc(r.reason) : '') + '</li>';
              })
              .join('') +
            '</ul></details>'
          : '';
        var excHtml = recs.excluded.length
          ? '<details class=collapse><summary>' + recs.excluded.length + ' excluded records</summary><ul class=idl>' +
            recs.excluded
              .map(function (r) {
                return '<li><b>' + esc(r.source_id || '') + '</b>' + (r.reason ? ' \u2014 ' + esc(r.reason) : '') + '</li>';
              })
              .join('') +
            '</ul></details>'
          : '';
        return ['context', summary + incHtml + excHtml];
      }
      if (s.role === 'orchestrator') {
        return ['orchestrator', 'tools: ' + ((s.tool_calls || []).join(', ') || '(none \u2014 straight to synthesis)')];
      }
      if (s.role === 'kb_search') {
        return [
          'kb_search',
          (s.hit ? 'HIT' : 'miss') +
            (s.fallback ? ' (deterministic fallback)' : '') +
            ' \u00b7 ' + esc(s.query || '') +
            ' \u00b7 ' + (s.chars || 0) + 'c'
        ];
      }
      if (s.role === 'medical_expert') return ['medical_expert', esc(s.note || '')];
      if (s.role === 'answer_synth') {
        return ['answer synth', esc(s.output || '') + (s.citations && s.citations.length ? '  [' + s.citations.join(',') + ']' : '')];
      }
      if (s.role === 'answer_resynth') return ['answer re-synth', esc(s.output || '')];
      if (s.role === 'answer_validator') {
        return [
          'answer validator' + (s.attempt ? ' #' + s.attempt : ''),
          (s.answer_ok ? 'PASS' : 'FLAG') + (s.answer_issues ? ' \u00b7 ' + esc(s.answer_issues) : ''),
          s.answer_ok ? 'ok' : s.answer_issues ? 'flag' : ''
        ];
      }
      if (s.role === 'indepth_synth') {
        return [
          'in-depth synth',
          (s.claims || [])
            .map(function (c) {
              return '\u2022 ' + esc(c);
            })
            .join('<br>') || '(no claims)'
        ];
      }
      if (s.role === 'indepth_resynth') {
        return [
          'in-depth re-synth',
          (s.claims || [])
            .map(function (c) {
              return '\u2022 ' + esc(c);
            })
            .join('<br>') || '(no claims)'
        ];
      }
      if (s.role === 'indepth_validator') {
        var f = s.flag || s.drop || [];
        return [
          'in-depth validator' + (s.attempt ? ' #' + s.attempt : ''),
          (s.flag ? 'flag ' : 'drop ') + JSON.stringify(f) + ' of ' + (s.claims_in || 0) + (s.issues ? ' \u00b7 ' + esc(s.issues) : ''),
          f.length ? 'flag' : 'ok'
        ];
      }
      return [s.role, esc(JSON.stringify(s))];
    };
    var steps = (tr.steps || [])
      .filter(function (s) {
        return s.role !== 'stage_timing';
      })
      .map(function (s) {
        var res = fmt(s);
        var label = res[0],
          body = res[1],
          tone = res[2];
        var kls = 'trole' + (tone === 'flag' ? ' flag' : tone === 'ok' ? ' ok' : '');
        var m = s.model ? '<span class=tmodel>' + esc(s.model) + '</span>' : '';
        return '<div class=tstep><div class="' + kls + '">' + esc(label) + m + '</div><div class=tbody>' + body + '</div></div>';
      })
      .join('<div class=tarrow>\u2193</div>');
    return '<div class=trace>' + (steps || '<div class=notrace>no steps</div>') + '</div>';
  }

  function renderStageTimings(rows) {
    if (!rows || !rows.length) return '';
    var body = rows
      .map(function (r) {
        return (
          '<tr><td>' +
          esc(String(r.stage || '').replace(/_/g, ' ') + (r.occurrence > 1 ? ' ' + r.occurrence : '')) +
          '</td><td>' + r.duration_ms + ' ms</td><td>' + esc(r.status || 'completed') + '</td></tr>'
        );
      })
      .join('');
    return (
      '<details class=stage-timings open><summary>stage timing breakdown</summary>' +
      '<table><thead><tr><th>stage</th><th>elapsed</th><th>status</th></tr></thead><tbody>' + body + '</tbody></table></details>'
    );
  }

  async function fetchStatus() {
    if (STATIC_DASHBOARD) return STATIC_DASHBOARD.status;
    var r = await fetch('/api/status');
    return await r.json();
  }

  async function fetchDetail(s, b) {
    if (STATIC_DASHBOARD) {
      var details = STATIC_DASHBOARD.details || {};
      return details[s + '|' + b] || { scenario: s, backend: b, turns: [] };
    }
    var r = await fetch('/api/detail?scenario=' + encodeURIComponent(s) + '&backend=' + encodeURIComponent(b));
    return await r.json();
  }

  async function tick() {
    var d;
    try {
      d = await fetchStatus();
    } catch (e) {
      return;
    }
    if (!d) return;
    var isCat = d.family === 'catalyst';
    document.querySelectorAll('section').forEach(function (s) {
      var h = s.querySelector('h2');
      if (!h) return;
      if (/^(Arms|Judged scores)/.test(h.textContent)) s.style.display = isCat ? 'none' : '';
    });
    var hdr = document.getElementById('hdr');
    var fill = document.getElementById('fill');
    var prog = document.getElementById('prog');
    var models = document.getElementById('models');
    var arms = document.getElementById('arms');
    var judges = document.getElementById('judges');
    var grid = document.getElementById('grid');
    var feed = document.getElementById('feed');

    if (!d.run) {
      if (hdr) hdr.textContent = 'waiting for a run...';
      return;
    }
    ARM_CARDS = d.arm_cards || {};
    LAST_STATUS = d;
    ARM_LABELS = {};
    Object.keys(d.arms || {}).forEach(function (b) {
      ARM_LABELS[b] = (d.arms[b] || {}).label;
    });
    var ed = loadEditorial();
    var pct = d.total ? Math.round((100 * d.done) / d.total) : 0;
    if (hdr) {
      var titlePrefix = ed && ed.title ? ed.title + '  \u00b7  ' : '';
      hdr.textContent = titlePrefix + 'run ' + d.run.slice(0, 8) + '  \u00b7  set ' + (d.set || '') + '  \u00b7  ' + pct + '%';
    }
    if (fill) fill.style.width = pct + '%';
    if (prog) prog.textContent = d.done + ' / ' + d.total + ' results';
    var wb = document.getElementById('warnbar');
    if (wb) {
      if (d.warning) {
        wb.textContent = d.warning;
        wb.style.display = '';
      } else {
        wb.style.display = 'none';
      }
    }
    var lg = document.getElementById('legend');
    if (lg) {
      if (isCat) {
        var t = '<b>' + (d.conformant || 0) + '</b> followed an allowed path &nbsp;\u00b7&nbsp; <b>' + (d.unexpected || 0) + '</b> unexpected behaviour';
        if (d.judged_scored) t += ' &nbsp;\u00b7&nbsp; judged <b>' + (d.judged_passed || 0) + '/' + d.judged_scored + '</b> \u2014 see the report';
        lg.innerHTML =
          t +
          '<br><span class=c200 style="padding:0 4px">\u2713</span> allowed path (a refusal, a question or a wrong answer still counts) &nbsp;\u00b7&nbsp; <span class=cerr style="padding:0 4px">\u00d7</span> the system misbehaved &nbsp;\u00b7&nbsp; <span class=crun style="padding:0 4px">\u25cf</span> running';
      } else {
        var L = (d.status_legend || [])
          .map(function (x) {
            return '<span class="gpill ' + toneCls(x.tone) + '">' + esc(x.symbol) + '</span> ' + esc(x.label);
          })
          .join(' &nbsp;');
        lg.innerHTML =
          'Each cell: <span class="gpill t-neutral">A</span> the Answer and <span class="gpill t-neutral">ID</span> the In-Depth, worst across the cell\'s turns; a number counts marked In-Depth points. ' +
          L +
          '<br>Corner mark: <span class=gconf>\u2713</span> the run followed an allowed path &nbsp;\u00b7&nbsp; <span class="gconf err">\u00d7</span> the system misbehaved (hover a cell for words).';
      }
    }
    if (models) {
      models.innerHTML =
        (d.models || [])
          .map(function (m) {
            return '<span class=chip title="' + esc(m.kind || '') + '">' + (m.kind ? '<span class=muted>' + esc(m.kind) + '</span> ' : '') + esc(m.id || m) + '</span>';
          })
          .join('') || '<span class=muted>no models recorded</span>';
    }
    if (arms) {
      arms.innerHTML = renderArmCards(d);
      restoreOpenDetails(arms);
    }
    if (judges) {
      judges.innerHTML = renderJudgeScores(d);
    }
    renderCheckPrecision(d);
    var gm = {};
    (d.grid || []).forEach(function (g) {
      gm[g.scenario + '|' + g.backend] = g;
    });
    var h =
      '<table class=grid><tr><th></th>' +
      (d.backends || [])
        .map(function (b) {
          return '<th title="' + esc(b) + '">' + esc(armTitle(b)) + '</th>';
        })
        .join('') +
      '</tr>';
    (d.scenarios || []).forEach(function (s) {
      h +=
        '<tr><th>' +
        esc(s) +
        '</th>' +
        (d.backends || [])
          .map(function (b) {
            var g = gm[s + '|' + b] || {};
            var st = g.state;
            var oc = st == null || st === 'pending' ? '' : ' onclick="openD(\'' + esc(s) + '\',\'' + esc(b) + '\')"';
            return gridCell(g, oc);
          })
          .join('') +
        '</tr>';
    });
    if (grid) grid.innerHTML = h + '</table>';
    if (feed) {
      feed.innerHTML = (d.feed || [])
        .slice()
        .reverse()
        .map(function (f) {
          return (
            '<div onclick="openD(\'' + esc(f.scenario) + '\',\'' + esc(f.backend) + '\')"><span class="' +
            (f.status === 200 ? 'ok' : 'err') + '">' + f.status + '</span> ' +
            esc(f.scenario) + '/' + esc(shortB(f.backend)) + ' t' + f.turn +
            ' <span class=muted>' + f.chars + 'c</span>' +
            (f.indepth_status != null
              ? ' <span class="' + (f.indepth_status === 200 && f.indepth_chars > 0 ? 'ok' : 'err') + '" title="In-Depth (separate call)">+ID ' + f.indepth_chars + 'c</span>'
              : '') +
            ' ' + esc(f.ans || '') + '</div>'
          );
        })
        .join('');
    }
  }

  window.openD = async function (s, b) {
    var d = await fetchDetail(s, b);
    var modal = document.getElementById('modal');
    var mbody = document.getElementById('mbody');
    if (!modal || !mbody) return;
    var e = d.expectations || {};
    var h = '<div class=mhead><b>' + esc(s) + '</b> &nbsp;\u00b7&nbsp; ' + esc(armTitle(b)) + ' <span class=muted>(' + esc(b) + ')</span><span class=x onclick="closeD()">\u2715</span></div>';
    var ce = d.catalystExpected;
    if (ce) {
      h += '<div class=exp><b>Question:</b> ' + esc(ce.question || '') + '<br>';
      h += '<b>Acceptance:</b> ' + esc(ce.criterion || '') + '<br>';
      h += '<b>Opening answer must be:</b> ' + esc(ce.baseOutcome || 'ready');
      (ce.turns || []).forEach(function (u, i) {
        h += '<br><b>Turn ' + (i + 2) + '</b> (\u201c' + esc(u.instruction || '') + '\u201d) \u2192 ' + esc(u.expectedOutcome || 'ready');
      });
      if (ce.goldCheck) {
        h +=
          '<br><b>Checked against:</b> ' + esc(ce.goldCheck.mode) +
          ' vs an independent reference<details><summary>reference SQL</summary><pre style="white-space:pre-wrap">' +
          esc(ce.goldCheck.referenceSql || '') + '</pre></details>';
      }
      h += '</div>';
    } else {
      h +=
        '<div class=exp><b>Expected:</b> ' +
        (e.should_abstain ? 'ABSTAIN' : 'retrieve') +
        (e.should_cite_resource_types ? ' [' + e.should_cite_resource_types.join(', ') + ']' : '') +
        '<br>' + esc(e.notes || '') + '</div>';
    }
    var jp = d.judge || {},
      jids = Object.keys(jp);
    if (jids.length) {
      h +=
        '<div class=exp><b>Judged:</b> ' +
        jids
          .map(function (a) {
            var r = jp[a];
            return (
              esc(a) + ' ' + fmt10(r.accuracy) + '/' + fmt10(r.completeness) + '/' + fmt10(r.relevance) +
              (r.harm ? ' HARM' : '') +
              (r.note ? ' \u2014 ' + esc(r.note) : '')
            );
          })
          .join('<br>') +
        '</div>';
    }
    var reps = d.turns || [];
    if (reps.length && reps[0].catalyst) {
      if (!ce && (reps[0].catalyst.question || reps[0].question)) {
        h += '<div class=exp><b>Question:</b> ' + esc(reps[0].catalyst.question || reps[0].question) + '</div>';
      }
      var chip = function (exp, obs) {
        return !exp || obs === exp
          ? '<span class=ok>' + esc(obs || '?') + '</span>'
          : '<span class=err>' + esc(obs || '?') + '</span>' + (exp ? ' <span class=muted>(expected ' + esc(exp) + ')</span>' : '');
      };
      var kindOf = function (o) {
        return o === 'needs_clarification'
          ? 'asked a question'
          : o === 'unsupported'
          ? 'declined'
          : o === 'rejected'
          ? 'was rejected'
          : 'wrote a query';
      };
      var say = function (role, label, body, extra) {
        return '<div class=tstep><div class="trole' + (extra || '') + '">' + esc(label) + '</div><div class=tbody>' + body + '</div></div>';
      };
      var arrow = '<div class=tarrow>\u2193</div>';
      reps.forEach(function (t) {
        var c = t.catalyst;
        var many = reps.length > 1;
        var head =
          (c.passed ? '<span class=ok>\u2713 judged pass</span>' : '<span class=err>\u00d7 judged fail</span>') +
          (c.conformed ? '' : ' <span class=err>\u00b7 the system misbehaved</span>') +
          ' <span class=muted>\u00b7 ' + Math.round((t.latency_ms || 0) / 1000) + 's</span>';
        if (many) h += '<div class=ctitle style="margin-top:8px">run ' + t.turn + '</div>';
        h += '<div class=meta>' + head + '</div>';
        var steps = [];
        steps.push(say('user', 'person asks', '<div class=q style="margin:0">' + esc(c.question || (d.catalystExpected || {}).question || '') + '</div>'));
        var sqlBlock = function (sql) {
          return '<pre class=sqlblock>' + esc(sql) + '</pre>';
        };
        var saidBlock = function (txt) {
          return '<pre style="white-space:pre-wrap;margin:0">' + esc(txt) + '</pre>';
        };
        var baseSql = c.baseSql || ((c.turns || []).length ? null : c.baseOutcome === 'ready' ? t.answer : null);
        var baseBody =
          (c.baseAnswerText ? saidBlock(c.baseAnswerText) : '') +
          (baseSql ? sqlBlock(baseSql) : '') +
          (!c.baseAnswerText && !baseSql ? '<span class=muted>(recorded before per-turn SQL; final query below)</span>' : '');
        steps.push(say('model', 'writer ' + kindOf(c.baseOutcome), baseBody + '<div class=meta style="margin-top:3px">' + chip(c.expectedBaseOutcome, c.baseOutcome) + '</div>'));
        (c.turns || []).forEach(function (u, i) {
          var isAnswer = c.baseOutcome === 'needs_clarification' && i === 0;
          steps.push(say('user', isAnswer ? 'person answers the question' : 'person asks for a change (turn ' + (i + 2) + ')', '<div class=q style="margin:0">' + esc(u.instruction || '') + '</div>'));
          var body =
            (u.answerText ? saidBlock(u.answerText) : '') +
            (u.sql ? sqlBlock(u.sql) : '') +
            (!u.answerText && !u.sql ? '<span class=muted>(recorded before per-turn SQL; final query below)</span>' : '');
          steps.push(say('model', 'writer ' + kindOf(u.observedOutcome), body + '<div class=meta style="margin-top:3px">' + chip(u.expectedOutcome, u.observedOutcome) + '</div>'));
        });
        h += '<div class=trace>' + steps.join(arrow) + '</div>';
        h += '<details class=tracebox open><summary>selected query and its result</summary><div class=turn>';
        h += '<div class=ans><pre style="white-space:pre-wrap;margin:0">' + esc(t.answer || '') + '</pre></div>';
        var rp = c.resultPreview;
        if (rp && (rp.columns || []).length) {
          h += '<div class=csec><div class=ctitle>Result (' + (rp.returned != null ? rp.returned + ' rows' : '') + (rp.truncatedPreview ? ', first 10 shown' : '') + ')</div>';
          h +=
            '<div style="overflow-x:auto"><table class=data><tr>' +
            rp.columns
              .map(function (cn) {
                return '<th>' + esc(cn) + '</th>';
              })
              .join('') +
            '</tr>';
          h += (rp.rows || [])
            .map(function (r) {
              return (
                '<tr>' +
                r
                  .map(function (v) {
                    return '<td>' + esc(v == null ? '\u2205' : String(v)) + '</td>';
                  })
                  .join('') +
                '</tr>'
              );
            })
            .join('');
          h += '</table></div></div>';
        }
        h += '</div></details>';
        var fa = c.failedAssertions || [];
        if (fa.length) {
          var conf = fa.filter(function (f) {
            return (f.class || 'conformance') === 'conformance';
          });
          var ev = fa.filter(function (f) {
            return (f.class || 'conformance') !== 'conformance';
          });
          if (conf.length) {
            h +=
              '<div class="caveat red"><b>Unexpected behaviour</b> \u2014 the run broke its own contract here, so this measurement is not trustworthy.</div>' +
              conf
                .map(function (f) {
                  return '<div class="caveat red"><b>' + esc(f.name) + '</b> \u2014 ' + esc(typeof f.evidence === 'string' ? f.evidence : JSON.stringify(f.evidence || '')) + '</div>';
                })
                .join('');
          }
          if (ev.length) {
            h +=
              '<details><summary>' + ev.length + ' judged check' + (ev.length > 1 ? 's' : '') + ' the answer did not meet</summary>' +
              ev
                .map(function (f) {
                  return '<div class=meta><b>' + esc(f.name) + '</b> \u2014 ' + esc(typeof f.evidence === 'string' ? f.evidence : JSON.stringify(f.evidence || '')) + '</div>';
                })
                .join('') +
              '</details>';
          }
        } else {
          h += '<div class=meta><span class=ok>every check passed</span></div>';
        }
      });
      mbody.innerHTML = h;
      modal.style.display = 'flex';
      return;
    }
    (d.turns || []).forEach(function (t) {
      var tr = t.trace;
      var av = t.answer_view,
        iv = t.indepth_view;
      h += '<div class=turn><div class=q>Turn ' + t.turn + ': ' + esc(t.question) + '</div>';
      h +=
        '<div class=meta><span class="' + (t.status === 200 ? 'ok' : 'err') + '">status ' + t.status + '</span> \u00b7 ' +
        fmtS(t.latency_ms || 0) + ' \u00b7 ' + (t.chars || 0) + ' chars \u00b7 ' + (t.citations || 0) + ' source refs</div>';
      h += renderStageTimings(tr && tr.stage_timings);
      if (t.error) {
        h += '<div class="ans err">' + esc(t.error) + '</div>';
      } else {
        var answerBody = esc(t.answer || (tr && tr.answer_text) || '') + renderBlocks(t.blocks, t.sources);
        if (av) {
          h += sectionHtml('Answer', av, answerBody);
          if (av.show_original) h += renderOriginalAnswer(t.answer_validation);
        } else {
          h += '<div class=csec><div class=ctitle>Answer</div><div class=ans>' + answerBody + '</div></div>';
        }
        if (iv) {
          var title = 'In-Depth' + (t.indepth_latency_ms ? ' <span class=muted>(separate call, ' + fmtS(t.indepth_latency_ms) + ')</span>' : '');
          var ivBodyHtml = renderMarkdown(iv.body_text || '');
          h += sectionHtml(title, iv, ivBodyHtml, renderClaims(iv) + renderDraft(iv, t.review_sources) + renderRawCheck(iv));
        }
      }
      h += renderSources(t.sources);
      h += renderRawRefs(resolveRefsList(t));
      h += '<details class=tracebox><summary>\u25b8 reasoning trace</summary>' + renderTrace(tr) + '</details>';
      h += '</div>';
    });
    mbody.innerHTML = h;
    modal.style.display = 'flex';
  };

  window.closeD = function () {
    var modal = document.getElementById('modal');
    if (modal) modal.style.display = 'none';
  };

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') window.closeD();
  });

  function initThemeToggle() {
    var key = 'oc-theme-dashboard';
    var btn = document.getElementById('oc-theme-toggle');
    if (!btn) return;
    function sync() {
      var cur = document.documentElement.getAttribute('data-theme') || 'dark';
      var next = cur === 'dark' ? 'light' : 'dark';
      btn.textContent = (cur === 'dark' ? '\u263e ' : '\u2600 ') + cur;
      btn.title = 'Switch to ' + next + ' theme';
      btn.setAttribute('aria-label', 'Color theme: ' + cur + '. Activate to switch to ' + next + ' theme.');
    }
    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') || 'dark';
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {}
      sync();
    });
    sync();
  }

  async function boot() {
    initThemeToggle();
    var el = document.getElementById('dashboard-data');
    if (el) {
      var raw = (el.textContent || '').trim();
      if (raw) {
        STATIC_DASHBOARD = JSON.parse(raw);
      } else {
        var src = el.getAttribute('data-src') || './dashboard-data.json';
        var res = await fetch(src);
        if (res.ok) {
          STATIC_DASHBOARD = await res.json();
        }
      }
      await tick();
      return;
    }
    await tick();
    setInterval(tick, 2000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
