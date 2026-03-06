#!/usr/bin/env python3
"""Local dashboard for self-optimizing loop data.

The server executes repository scripts (`metrics_report.sh`, `weekly_review.sh`,
and `optimize_skill.sh`) and exposes a filterable UI for date ranges, skill
selection, metric keys, optimization discovery, and manual optimization trigger.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AOSO Dashboard</title>
  <style>
    :root {
      --bg: #f8f6f2;
      --panel: #fffefb;
      --ink: #1f2a30;
      --muted: #56656e;
      --line: #d8d2c9;
      --accent: #197278;
      --accent-soft: #d7ecee;
      --warn: #cb4b16;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 20% 0%, #fef7e4 0%, transparent 45%),
        radial-gradient(circle at 90% 20%, #e5f3ff 0%, transparent 40%),
        var(--bg);
    }
    .wrap {
      max-width: 1100px;
      margin: 32px auto;
      padding: 0 16px 32px;
    }
    .hero {
      background: linear-gradient(120deg, #f4ede0, #eaf8f8);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 18px;
    }
    .hero h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: -0.02em;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }
    .filters, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }
    label {
      display: flex;
      flex-direction: column;
      font-size: 12px;
      color: var(--muted);
      gap: 6px;
    }
    input, select, button {
      font: inherit;
      border-radius: 9px;
      border: 1px solid var(--line);
      padding: 9px 10px;
      background: #fff;
      color: var(--ink);
    }
    input:focus, select:focus, button:focus {
      outline: 2px solid var(--accent-soft);
      outline-offset: 1px;
    }
    button {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      align-self: end;
    }
    .meta {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 10px;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 10px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }
    .card .k {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .card .v {
      font-size: 18px;
      font-weight: 700;
      line-height: 1.15;
      word-break: break-word;
    }
    .list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 13px;
    }
    .op-wrap {
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .op-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }
    .op-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .op-title {
      font-size: 14px;
      font-weight: 700;
      margin: 0;
      word-break: break-word;
    }
    .badge {
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 700;
      border: 1px solid var(--line);
      background: #f7f3eb;
      color: #4f5c64;
      white-space: nowrap;
    }
    .badge.needs_optimization { background: #fff0e8; color: #8b2d00; border-color: #f2c2a5; }
    .badge.watch { background: #fff8e7; color: #7a5200; border-color: #e7cd8e; }
    .badge.healthy { background: #e9f8ef; color: #1f6b39; border-color: #b6debf; }
    .badge.no_data { background: #eef2f5; color: #5f6e79; border-color: #d3dde4; }
    .op-score {
      color: var(--muted);
      font-size: 12px;
      margin: 0 0 8px;
    }
    .mini-list {
      margin: 0;
      padding-left: 16px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }
    .trigger-btn {
      margin-top: 8px;
      width: 100%;
      border-color: #8f2d56;
      background: #8f2d56;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }
    .trigger-btn[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .rec-wrap {
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .rec-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }
    .code-chip {
      display: block;
      margin-top: 8px;
      padding: 8px;
      border-radius: 8px;
      background: #f2efe8;
      border: 1px solid #dbd2c3;
      color: #2b3338;
      font-size: 12px;
      font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      white-space: pre-wrap;
      word-break: break-word;
    }
    details {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      margin-top: 10px;
      background: #fff;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      color: #20333f;
    }
    .hint {
      color: var(--warn);
      font-size: 12px;
      min-height: 16px;
      margin-top: 8px;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .op-wrap { grid-template-columns: 1fr; }
      .rec-wrap { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      .grid { grid-template-columns: 1fr; }
      .cards { grid-template-columns: 1fr; }
      .hero h1 { font-size: 24px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1 data-i18n="hero_title">Self-Optimizing Loop Dashboard</h1>
      <p data-i18n="hero_subtitle">Filter by date, skill, cutover, and metric key. The page executes local project scripts to load data.</p>
    </section>

    <section class="filters">
      <div class="grid">
        <label><span data-i18n="label_start_date">Start Date</span>
          <input id="startDate" type="date" />
        </label>
        <label><span data-i18n="label_end_date">End Date</span>
          <input id="endDate" type="date" />
        </label>
        <label><span data-i18n="label_cutover">Cutover</span>
          <input id="cutoverDate" type="date" />
        </label>
        <label><span data-i18n="label_skill">Skill</span>
          <select id="skillName"><option value="">(all)</option></select>
        </label>
        <label><span data-i18n="label_metric_filter">Metric Key Filter</span>
          <input id="metricFilter" type="text" placeholder="token|duration|success" data-i18n-placeholder="placeholder_metric_filter" />
        </label>
        <label><span data-i18n="label_language">Language</span>
          <select id="languageSelect">
            <option value="en">English</option>
            <option value="zh">中文</option>
          </select>
        </label>
      </div>
      <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <button id="refreshBtn" type="button" data-i18n="btn_refresh">Refresh Dashboard</button>
      </div>
      <div class="hint" id="hint"></div>
    </section>

    <section class="panel">
      <div class="meta" id="metaText" data-i18n="meta_loading">Loading...</div>
      <div class="cards" id="cards"></div>
      <ul class="list" id="sections"></ul>
      <h3 style="margin: 12px 0 8px; font-size: 16px;" data-i18n="title_skill_opt_discovery">Skill Optimization Discovery</h3>
      <div class="op-wrap" id="opportunities"></div>
      <h3 style="margin: 12px 0 8px; font-size: 16px;" data-i18n="title_new_skill_recommendations">New Skill Recommendations</h3>
      <div class="rec-wrap" id="newSkillRecommendations"></div>
      <details>
        <summary data-i18n="summary_opt_log">Optimization Trigger Log</summary>
        <pre id="optimizeLog"></pre>
      </details>
      <details>
        <summary data-i18n="summary_raw_overall">Raw Overall Output</summary>
        <pre id="overallRaw"></pre>
      </details>
      <details>
        <summary data-i18n="summary_raw_skill">Raw Skill Output</summary>
        <pre id="skillRaw"></pre>
      </details>
      <details>
        <summary data-i18n="summary_weekly_review">Weekly Review (Last 7 Days of Selected Range)</summary>
        <pre id="weeklyRaw"></pre>
      </details>
    </section>
  </div>

  <script>
    const I18N = {
      en: {
        hero_title: "Self-Optimizing Loop Dashboard",
        hero_subtitle: "Filter by date, skill, cutover, and metric key. The page executes local project scripts to load data.",
        label_start_date: "Start Date",
        label_end_date: "End Date",
        label_cutover: "Cutover",
        label_skill: "Skill",
        label_metric_filter: "Metric Key Filter",
        placeholder_metric_filter: "token|duration|success",
        label_language: "Language",
        btn_refresh: "Refresh Dashboard",
        meta_loading: "Loading...",
        title_skill_opt_discovery: "Skill Optimization Discovery",
        title_new_skill_recommendations: "New Skill Recommendations",
        summary_opt_log: "Optimization Trigger Log",
        summary_raw_overall: "Raw Overall Output",
        summary_raw_skill: "Raw Skill Output",
        summary_weekly_review: "Weekly Review (Last 7 Days of Selected Range)",
        option_all: "(all)",
        status_unknown: "unknown",
        status_no_data: "no data",
        status_healthy: "healthy",
        status_watch: "watch",
        status_needs_optimization: "needs optimization",
        msg_no_metrics_match: "No metrics matched filter.",
        msg_no_skill_rows: "No skill rows for selected range.",
        msg_no_new_skill_rec: "No new skill recommendation in selected range.",
        label_findings: "Findings",
        label_suggested_actions: "Suggested actions",
        label_top_root_causes: "Top root causes",
        label_suggested_new_skill: "Suggested new skill",
        label_score: "score",
        label_sample: "sample",
        label_coverage: "coverage",
        label_rows: "rows",
        label_data_file: "data_file",
        label_generated_at: "generated_at",
        btn_trigger_opt: "Trigger Self-Optimization",
        btn_running: "Running...",
        btn_triggered: "Triggered",
        msg_no_skill_query: "(no skill query)",
        msg_empty: "(empty)",
        msg_load_failed: "Load failed",
        msg_init_failed: "Initialization failed",
        msg_opt_failed: "Optimize failed",
        log_skill: "skill",
        log_status: "status",
        log_score: "score",
        log_report: "report",
        label_metrics_count: "metrics",
        label_none: "none",
      },
      zh: {
        hero_title: "自优化闭环看板",
        hero_subtitle: "按日期、skill、cutover 和指标关键字筛选。页面会执行项目脚本获取数据。",
        label_start_date: "开始日期",
        label_end_date: "结束日期",
        label_cutover: "切换日期",
        label_skill: "技能",
        label_metric_filter: "指标关键字筛选",
        placeholder_metric_filter: "token|duration|success",
        label_language: "语言",
        btn_refresh: "刷新看板",
        meta_loading: "加载中...",
        title_skill_opt_discovery: "现有 Skill 优化发现",
        title_new_skill_recommendations: "新增 Skill 推荐",
        summary_opt_log: "优化触发日志",
        summary_raw_overall: "总体原始输出",
        summary_raw_skill: "单 Skill 原始输出",
        summary_weekly_review: "周报（筛选区间内最近 7 天）",
        option_all: "（全部）",
        status_unknown: "未知",
        status_no_data: "无数据",
        status_healthy: "健康",
        status_watch: "观察",
        status_needs_optimization: "需要优化",
        msg_no_metrics_match: "没有匹配筛选条件的指标。",
        msg_no_skill_rows: "当前筛选区间没有 skill 数据。",
        msg_no_new_skill_rec: "当前筛选区间暂无新增 skill 推荐。",
        label_findings: "发现",
        label_suggested_actions: "建议动作",
        label_top_root_causes: "高频根因",
        label_suggested_new_skill: "建议新增 skill 名称",
        label_score: "评分",
        label_sample: "样本",
        label_coverage: "覆盖率",
        label_rows: "行数",
        label_data_file: "数据文件",
        label_generated_at: "生成时间",
        btn_trigger_opt: "触发自优化",
        btn_running: "执行中...",
        btn_triggered: "已触发",
        msg_no_skill_query: "（未指定 skill 查询）",
        msg_empty: "（空）",
        msg_load_failed: "加载失败",
        msg_init_failed: "初始化失败",
        msg_opt_failed: "优化触发失败",
        log_skill: "skill",
        log_status: "状态",
        log_score: "评分",
        log_report: "报告",
        label_metrics_count: "指标",
        label_none: "无",
      },
    };

    let currentLang = localStorage.getItem("aoso_dashboard_lang") || "en";
    if (!I18N[currentLang]) currentLang = "en";
    let lastReport = null;

    function t(key) {
      const dict = I18N[currentLang] || I18N.en;
      return dict[key] || I18N.en[key] || key;
    }

    function applyLanguage() {
      document.documentElement.lang = currentLang === "zh" ? "zh-CN" : "en";
      for (const el of document.querySelectorAll("[data-i18n]")) {
        el.textContent = t(el.dataset.i18n);
      }
      for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
        el.placeholder = t(el.dataset.i18nPlaceholder);
      }
    }

    const nodes = {
      startDate: document.getElementById("startDate"),
      endDate: document.getElementById("endDate"),
      cutoverDate: document.getElementById("cutoverDate"),
      skillName: document.getElementById("skillName"),
      languageSelect: document.getElementById("languageSelect"),
      metricFilter: document.getElementById("metricFilter"),
      refreshBtn: document.getElementById("refreshBtn"),
      hint: document.getElementById("hint"),
      cards: document.getElementById("cards"),
      sections: document.getElementById("sections"),
      opportunities: document.getElementById("opportunities"),
      newSkillRecommendations: document.getElementById("newSkillRecommendations"),
      optimizeLog: document.getElementById("optimizeLog"),
      overallRaw: document.getElementById("overallRaw"),
      skillRaw: document.getElementById("skillRaw"),
      weeklyRaw: document.getElementById("weeklyRaw"),
      metaText: document.getElementById("metaText"),
    };

    async function fetchJSON(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }

    function renderOptions(payload) {
      nodes.startDate.value = payload.default_start || "";
      nodes.endDate.value = payload.default_end || "";
      nodes.cutoverDate.value = payload.default_cutover || "";
      const current = nodes.skillName.value;
      nodes.skillName.innerHTML = `<option value="">${t("option_all")}</option>`;
      for (const skill of payload.skills || []) {
        const opt = document.createElement("option");
        opt.value = skill;
        opt.textContent = skill;
        if (skill === current) opt.selected = true;
        nodes.skillName.appendChild(opt);
      }
    }

    function matchMetricFilter(key, query) {
      if (!query) return true;
      return key.toLowerCase().includes(query.toLowerCase());
    }

    function renderCards(metrics, metricFilter) {
      nodes.cards.innerHTML = "";
      const entries = Object.entries(metrics || {}).filter(([k]) => matchMetricFilter(k, metricFilter));
      if (entries.length === 0) {
        nodes.cards.innerHTML = `<div class="card"><div class="k">${t("log_status")}</div><div class="v">${t("msg_no_metrics_match")}</div></div>`;
        return;
      }
      for (const [key, value] of entries) {
        const el = document.createElement("div");
        el.className = "card";
        el.innerHTML = `<div class="k">${key}</div><div class="v">${value}</div>`;
        nodes.cards.appendChild(el);
      }
    }

    function renderSections(sections) {
      nodes.sections.innerHTML = "";
      for (const sec of sections || []) {
        const li = document.createElement("li");
        li.textContent = `${sec.title} (${Object.keys(sec.metrics || {}).length} ${t("label_metrics_count")})`;
        nodes.sections.appendChild(li);
      }
    }

    function statusLabel(raw) {
      if (!raw) return t("status_unknown");
      return t(`status_${raw}`);
    }

    function renderOpportunities(items) {
      nodes.opportunities.innerHTML = "";
      if (!items || items.length === 0) {
        nodes.opportunities.innerHTML =
          `<div class="op-card"><p class="op-title">${t("msg_no_skill_rows")}</p></div>`;
        return;
      }
      for (const item of items) {
        const card = document.createElement("div");
        card.className = "op-card";
        const reasons = (item.reasons || []).map((r) => `<li>${r}</li>`).join("");
        const actions = (item.suggested_actions || []).map((a) => `<li>${a}</li>`).join("");
        const roots = (item.top_root_causes || []).map((c) => `<li>${c}</li>`).join("");
        const status = item.status || "unknown";
        const disabled = item.can_trigger ? "" : "disabled";
        card.innerHTML = `
          <div class="op-head">
            <p class="op-title">${item.skill}</p>
            <span class="badge ${status}">${statusLabel(status)}</span>
          </div>
          <p class="op-score">${t("label_score")}=${item.score} | ${t("label_sample")}=${item.sample_size_skill}</p>
          <div style="font-size:12px; margin-bottom:6px;">${t("label_findings")}</div>
          <ul class="mini-list">${reasons || `<li>${t("label_none")}</li>`}</ul>
          <div style="font-size:12px; margin:8px 0 6px;">${t("label_suggested_actions")}</div>
          <ul class="mini-list">${actions || `<li>${t("label_none")}</li>`}</ul>
          <div style="font-size:12px; margin:8px 0 6px;">${t("label_top_root_causes")}</div>
          <ul class="mini-list">${roots || `<li>${t("label_none")}</li>`}</ul>
          <button class="trigger-btn" data-skill="${item.skill}" data-default-label="${t("btn_trigger_opt")}" ${disabled}>${t("btn_trigger_opt")}</button>
        `;
        nodes.opportunities.appendChild(card);
      }
    }

    function renderNewSkillRecommendations(items) {
      nodes.newSkillRecommendations.innerHTML = "";
      if (!items || items.length === 0) {
        nodes.newSkillRecommendations.innerHTML =
          `<div class="rec-card"><p class="op-title">${t("msg_no_new_skill_rec")}</p></div>`;
        return;
      }
      for (const item of items) {
        const card = document.createElement("div");
        card.className = "rec-card";
        const findings = (item.findings || []).map((f) => `<li>${f}</li>`).join("");
        const actions = (item.suggested_actions || []).map((a) => `<li>${a}</li>`).join("");
        const roots = (item.top_root_causes || []).map((c) => `<li>${c}</li>`).join("");
        const status = item.status || "watch";
        card.innerHTML = `
          <div class="op-head">
            <p class="op-title">${item.task_type}</p>
            <span class="badge ${status}">${statusLabel(status)}</span>
          </div>
          <p class="op-score">${t("label_score")}=${item.score} | ${t("label_sample")}=${item.sample_size} | ${t("label_coverage")}=${item.skill_coverage_pct}</p>
          <div style="font-size:12px; margin-bottom:6px;">${t("label_suggested_new_skill")}</div>
          <div class="code-chip">${item.suggested_skill_name}</div>
          <div style="font-size:12px; margin:8px 0 6px;">${t("label_findings")}</div>
          <ul class="mini-list">${findings || `<li>${t("label_none")}</li>`}</ul>
          <div style="font-size:12px; margin:8px 0 6px;">${t("label_suggested_actions")}</div>
          <ul class="mini-list">${actions || `<li>${t("label_none")}</li>`}</ul>
          <div style="font-size:12px; margin:8px 0 6px;">${t("label_top_root_causes")}</div>
          <ul class="mini-list">${roots || `<li>${t("label_none")}</li>`}</ul>
        `;
        nodes.newSkillRecommendations.appendChild(card);
      }
    }

    async function triggerOptimization(skill) {
      const payload = {
        skill,
        start: nodes.startDate.value || "",
        end: nodes.endDate.value || "",
        cutover: nodes.cutoverDate.value || "",
      };
      const response = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const data = await response.json();
      const now = new Date().toISOString();
      const line = [
        `[${now}] ${t("log_skill")}=${skill}`,
        `${t("log_status")}=${data.optimization_status || t("status_unknown")}`,
        `${t("log_score")}=${data.opportunity_score || "n/a"}`,
        `${t("log_report")}=${data.report_file || "n/a"}`,
      ].join(" | ");
      nodes.optimizeLog.textContent = `${line}\n${nodes.optimizeLog.textContent || ""}`.trim();
      return data;
    }

    async function refreshDashboard() {
      nodes.hint.textContent = "";
      const params = new URLSearchParams();
      if (nodes.startDate.value) params.set("start", nodes.startDate.value);
      if (nodes.endDate.value) params.set("end", nodes.endDate.value);
      if (nodes.cutoverDate.value) params.set("cutover", nodes.cutoverDate.value);
      if (nodes.skillName.value) params.set("skill", nodes.skillName.value);
      const metricFilter = nodes.metricFilter.value.trim();

      try {
        const report = await fetchJSON(`/api/report?${params.toString()}`);
        const metrics = report.flat_metrics || {};
        renderCards(metrics, metricFilter);
        renderSections(report.sections || []);
        renderOpportunities(report.opportunities || []);
        renderNewSkillRecommendations(report.new_skill_recommendations || []);
        nodes.overallRaw.textContent = report.overall_raw || "";
        nodes.skillRaw.textContent = report.skill_raw || t("msg_no_skill_query");
        nodes.weeklyRaw.textContent = report.weekly_raw || t("msg_empty");
        nodes.metaText.textContent =
          `${t("label_rows")}=${report.row_count} | ${t("label_data_file")}=${report.data_file} | ${t("label_generated_at")}=${report.generated_at}`;
        lastReport = report;
      } catch (err) {
        nodes.hint.textContent = `${t("msg_load_failed")}: ${err.message}`;
      }
    }

    async function boot() {
      try {
        const options = await fetchJSON("/api/options");
        nodes.languageSelect.value = currentLang;
        applyLanguage();
        renderOptions(options);
        await refreshDashboard();
      } catch (err) {
        nodes.hint.textContent = `${t("msg_init_failed")}: ${err.message}`;
      }
    }

    nodes.refreshBtn.addEventListener("click", refreshDashboard);
    nodes.languageSelect.addEventListener("change", () => {
      currentLang = nodes.languageSelect.value === "zh" ? "zh" : "en";
      localStorage.setItem("aoso_dashboard_lang", currentLang);
      applyLanguage();
      if (lastReport) {
        renderOptions({
          default_start: nodes.startDate.value,
          default_end: nodes.endDate.value,
          default_cutover: nodes.cutoverDate.value,
          skills: Array.from(nodes.skillName.options).map((o) => o.value).filter(Boolean),
        });
        renderCards(lastReport.flat_metrics || {}, nodes.metricFilter.value.trim());
        renderSections(lastReport.sections || []);
        renderOpportunities(lastReport.opportunities || []);
        renderNewSkillRecommendations(lastReport.new_skill_recommendations || []);
        nodes.skillRaw.textContent = lastReport.skill_raw || t("msg_no_skill_query");
        nodes.weeklyRaw.textContent = lastReport.weekly_raw || t("msg_empty");
        nodes.metaText.textContent =
          `${t("label_rows")}=${lastReport.row_count} | ${t("label_data_file")}=${lastReport.data_file} | ${t("label_generated_at")}=${lastReport.generated_at}`;
      }
    });
    nodes.opportunities.addEventListener("click", async (event) => {
      const btn = event.target.closest(".trigger-btn");
      if (!btn) return;
      const skill = btn.getAttribute("data-skill");
      if (!skill) return;
      btn.disabled = true;
      const old = btn.getAttribute("data-default-label") || t("btn_trigger_opt");
      btn.textContent = t("btn_running");
      try {
        await triggerOptimization(skill);
        btn.textContent = t("btn_triggered");
      } catch (err) {
        nodes.hint.textContent = `${t("msg_opt_failed")}: ${err.message}`;
        btn.textContent = old;
      } finally {
        setTimeout(() => {
          btn.disabled = false;
          btn.textContent = old;
        }, 1200);
      }
    });
    boot();
  </script>
</body>
</html>
"""


def _is_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


@dataclass
class RuntimePaths:
    data_file: Path
    kb_dir: Path
    report_dir: Path
    metrics_script: Path
    weekly_script: Path
    optimize_script: Path


def resolve_runtime_paths() -> RuntimePaths:
    script_dir = Path(__file__).resolve().parent
    skill_mode = (script_dir.parent / "SKILL.md").is_file()
    workspace = Path(os.environ.get("AOSO_WORKSPACE_DIR", os.getcwd())).resolve()

    if skill_mode:
        data_file_default = workspace / ".agent-loop-data/metrics/task-runs.csv"
        kb_dir_default = workspace / ".agent-loop-data/knowledge-base/errors"
        report_dir_default = workspace / ".agent-loop-data/reports"
    else:
        root_dir = script_dir.parent
        data_file_default = root_dir / "metrics/task-runs.csv"
        kb_dir_default = root_dir / "knowledge-base/errors"
        report_dir_default = root_dir / "reports"

    data_file = Path(os.environ.get("AOSO_DATA_FILE", str(data_file_default))).resolve()
    kb_dir = Path(os.environ.get("AOSO_KB_DIR", str(kb_dir_default))).resolve()
    report_dir = Path(os.environ.get("AOSO_REPORT_DIR", str(report_dir_default))).resolve()

    return RuntimePaths(
        data_file=data_file,
        kb_dir=kb_dir,
        report_dir=report_dir,
        metrics_script=script_dir / "metrics_report.sh",
        weekly_script=script_dir / "weekly_review.sh",
        optimize_script=script_dir / "optimize_skill.sh",
    )


def run_script(command: Sequence[str], env_overrides: Dict[str, str]) -> str:
    env = os.environ.copy()
    env.update(env_overrides)
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(output.strip() or f"command failed: {' '.join(command)}")
    return output.strip()


def read_task_rows(data_file: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not data_file.exists():
        return [], []
    with data_file.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames or []
        rows = [row for row in reader]
    return fieldnames, rows


def filter_rows(
    rows: Sequence[Dict[str, str]], start: str, end: str
) -> List[Dict[str, str]]:
    filtered: List[Dict[str, str]] = []
    for row in rows:
        row_date = row.get("date", "")
        if not _is_date(row_date):
            continue
        if start and row_date < start:
            continue
        if end and row_date > end:
            continue
        filtered.append(row)
    return filtered


def write_filtered_csv(
    fieldnames: Sequence[str], rows: Sequence[Dict[str, str]], tmp_file: Path
) -> None:
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    with tmp_file.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_metrics_output(text: str) -> List[Dict[str, object]]:
    sections: List[Dict[str, object]] = []
    title = None
    metrics: Dict[str, str] = {}

    def flush() -> None:
        nonlocal title, metrics
        if title is not None:
            sections.append({"title": title, "metrics": dict(metrics)})
        title = None
        metrics = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  "):
            clean = line.strip()
            if ": " in clean and title is not None:
                key, value = clean.split(": ", 1)
                metrics[key] = value
            continue
        flush()
        title = line
    flush()
    return sections


def flatten_metrics(sections: Sequence[Dict[str, object]]) -> Dict[str, str]:
    flat: Dict[str, str] = {}
    for section in sections:
        title = str(section.get("title", "section"))
        metrics = section.get("metrics", {})
        if not isinstance(metrics, dict):
            continue
        for key, value in metrics.items():
            if title.startswith("Overall Metrics"):
                flat[key] = str(value)
            elif title.startswith("Pre/Post Metrics"):
                flat[key] = str(value)
            elif title.startswith("Skill: "):
                skill_name = title.replace("Skill: ", "", 1)
                flat[f"{skill_name}.{key}"] = str(value)
    return flat


def collect_skills(rows: Sequence[Dict[str, str]]) -> List[str]:
    skill_set = {
        row.get("skill_name", "").strip()
        for row in rows
        if row.get("used_skill", "").strip().lower() == "true" and row.get("skill_name", "").strip()
    }
    return sorted(skill_set)


def _parse_percent(value: str) -> Optional[float]:
    if not value or value == "n/a":
        return None
    raw = value.strip().replace("%", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_pp(value: str) -> Optional[float]:
    if not value or value == "n/a":
        return None
    raw = value.strip().replace("pp", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_float(value: str) -> Optional[float]:
    if not value or value == "n/a":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def _parse_int(value: str) -> Optional[int]:
    if not value or value == "n/a":
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def _unique_ordered(values: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _row_int(row: Dict[str, str], key: str) -> int:
    value = row.get(key, "").strip()
    try:
        return int(value)
    except ValueError:
        return 0


def _row_used_skill(row: Dict[str, str]) -> bool:
    return row.get("used_skill", "").strip().lower() == "true"


def _row_success(row: Dict[str, str]) -> bool:
    return row.get("success", "").strip().lower() == "true"


def _to_kebab(value: str) -> str:
    chars: List[str] = []
    for ch in value.strip().lower():
        if ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    raw = "".join(chars)
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw.strip("-") or "workflow"


def _top_root_causes_for_task_type(
    task_type: str, kb_entries: Sequence[Dict[str, str]]
) -> List[str]:
    counter: Counter[str] = Counter()
    for entry in kb_entries:
        if entry.get("task_type", "").strip() != task_type:
            continue
        cause = entry.get("root_cause", "").strip()
        if cause:
            counter[cause] += 1
    return [f"{count}x {cause}" for cause, count in counter.most_common(3)]


def _count_from_root_cause_label(value: str) -> int:
    prefix = value.split("x ", 1)[0].strip()
    try:
        return int(prefix)
    except ValueError:
        return 0


def discover_new_skill_recommendations(
    filtered_rows: Sequence[Dict[str, str]],
    kb_entries: Sequence[Dict[str, str]],
) -> List[Dict[str, object]]:
    if not filtered_rows:
        return []

    existing_skills = set(collect_skills(filtered_rows))

    total_tokens = sum(_row_int(row, "total_tokens") for row in filtered_rows)
    total_duration = sum(_row_int(row, "duration_sec") for row in filtered_rows)
    total_rows = len(filtered_rows)
    overall_avg_tokens = (total_tokens / total_rows) if total_rows > 0 else 0.0
    overall_avg_duration = (total_duration / total_rows) if total_rows > 0 else 0.0
    overall_fail_rate = (
        sum(1 for row in filtered_rows if not _row_success(row)) / total_rows
        if total_rows > 0
        else 0.0
    )
    overall_rework_rate = (
        sum(_row_int(row, "rework_count") for row in filtered_rows) / total_rows
        if total_rows > 0
        else 0.0
    )

    by_task_all: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    by_task_no_skill: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in filtered_rows:
        task_type = row.get("task_type", "").strip()
        if not task_type:
            continue
        by_task_all[task_type].append(row)
        if not _row_used_skill(row):
            by_task_no_skill[task_type].append(row)

    recommendations: List[Dict[str, object]] = []
    for task_type, rows in by_task_no_skill.items():
        if not rows:
            continue
        sample_size = len(rows)
        all_rows_for_type = by_task_all.get(task_type, [])
        skill_used_count = sum(1 for row in all_rows_for_type if _row_used_skill(row))
        coverage = (
            (skill_used_count / len(all_rows_for_type)) * 100
            if all_rows_for_type
            else 0.0
        )

        avg_tokens = sum(_row_int(row, "total_tokens") for row in rows) / sample_size
        avg_duration = sum(_row_int(row, "duration_sec") for row in rows) / sample_size
        fail_rate = sum(1 for row in rows if not _row_success(row)) / sample_size
        rework_rate = sum(_row_int(row, "rework_count") for row in rows) / sample_size
        top_root_causes = _top_root_causes_for_task_type(task_type, kb_entries)
        recurring_root_cause = any(
            _count_from_root_cause_label(cause) >= 2 for cause in top_root_causes
        )

        score = 0
        findings: List[str] = []
        actions: List[str] = []

        if sample_size >= 3:
            score += 40
            findings.append(f"Workflow repeats frequently without skill (count={sample_size}).")
            actions.append("Create a dedicated skill workflow for this task type.")

        if overall_avg_tokens > 0 and avg_tokens >= overall_avg_tokens * 1.2 and sample_size >= 3:
            score += 25
            findings.append(
                f"Token cost is high for no-skill runs (avg={avg_tokens:.2f}, overall={overall_avg_tokens:.2f})."
            )
            actions.append("Move deterministic steps into scripts and keep prompts minimal.")

        if overall_avg_duration > 0 and avg_duration >= overall_avg_duration * 1.2 and sample_size >= 3:
            score += 15
            findings.append(
                f"Duration is high for no-skill runs (avg={avg_duration:.2f}, overall={overall_avg_duration:.2f})."
            )
            actions.append("Design a shorter skill path with explicit checkpoints.")

        if fail_rate >= max(0.2, overall_fail_rate + 0.1) and sample_size >= 3:
            score += 20
            findings.append(
                f"Failure rate is high (task={fail_rate * 100:.2f}%, overall={overall_fail_rate * 100:.2f}%)."
            )
            actions.append("Add stronger validation and recovery steps in the new skill.")

        if rework_rate >= overall_rework_rate + 0.5 and sample_size >= 3:
            score += 15
            findings.append(
                f"Rework rate is elevated (task={rework_rate:.2f}, overall={overall_rework_rate:.2f})."
            )
            actions.append("Include prevention rules and trigger signals in skill guidance.")

        if recurring_root_cause:
            score += 30
            findings.append("Root cause recurs for this task type in error KB.")
            actions.append("Capture recurring root-cause handling directly in the new skill.")

        suggested_skill_name = _to_kebab(f"{task_type}-workflow-optimizer")
        if suggested_skill_name in existing_skills:
            continue

        if score < 50:
            continue

        if score >= 70:
            status = "needs_optimization"
        else:
            status = "watch"

        if coverage >= 70.0:
            # This task type is already covered by existing skills frequently.
            continue

        recommendations.append(
            {
                "task_type": task_type,
                "suggested_skill_name": suggested_skill_name,
                "status": status,
                "score": score,
                "sample_size": sample_size,
                "skill_coverage_pct": f"{coverage:.2f}%",
                "avg_tokens": f"{avg_tokens:.2f}",
                "avg_duration_sec": f"{avg_duration:.2f}",
                "fail_rate_pct": f"{fail_rate * 100:.2f}%",
                "rework_rate": f"{rework_rate:.3f}",
                "findings": _unique_ordered(findings),
                "suggested_actions": _unique_ordered(actions),
                "top_root_causes": top_root_causes,
            }
        )

    recommendations.sort(key=lambda item: int(item.get("score", 0)), reverse=True)
    return recommendations


def load_kb_entries(kb_dir: Path, start: str, end: str) -> List[Dict[str, str]]:
    if not kb_dir.exists():
        return []

    entries: List[Dict[str, str]] = []
    for md in kb_dir.glob("*.md"):
        fields: Dict[str, str] = {"date": "", "task_type": "", "root_cause": ""}
        try:
            with md.open("r", encoding="utf-8") as fp:
                for raw in fp:
                    line = raw.strip()
                    if line.startswith("date: "):
                        fields["date"] = line.replace("date: ", "", 1).strip()
                    elif line.startswith("task_type: "):
                        fields["task_type"] = line.replace("task_type: ", "", 1).strip()
                    elif line.startswith("root_cause: "):
                        fields["root_cause"] = line.replace("root_cause: ", "", 1).strip()
                    if fields["date"] and fields["task_type"] and fields["root_cause"]:
                        break
        except UnicodeDecodeError:
            continue
        row_date = fields.get("date", "")
        if not _is_date(row_date):
            continue
        if start and row_date < start:
            continue
        if end and row_date > end:
            continue
        if not fields.get("task_type") or not fields.get("root_cause"):
            continue
        entries.append(fields)
    return entries


def _find_skill_metrics(
    sections: Sequence[Dict[str, object]], skill: str
) -> Dict[str, str]:
    for section in sections:
        title = str(section.get("title", ""))
        if title == f"Skill: {skill}":
            metrics = section.get("metrics", {})
            if isinstance(metrics, dict):
                return {str(k): str(v) for k, v in metrics.items()}
    return {}


def _top_root_causes_for_skill(
    skill_rows: Sequence[Dict[str, str]], kb_entries: Sequence[Dict[str, str]]
) -> List[str]:
    task_types = {
        row.get("task_type", "").strip()
        for row in skill_rows
        if row.get("task_type", "").strip()
    }
    if not task_types:
        return []
    counter: Counter[str] = Counter()
    for entry in kb_entries:
        task_type = entry.get("task_type", "").strip()
        if task_type not in task_types:
            continue
        cause = entry.get("root_cause", "").strip()
        if cause:
            counter[cause] += 1
    return [f"{count}x {cause}" for cause, count in counter.most_common(3)]


def build_skill_opportunity(
    skill: str,
    metrics: Dict[str, str],
    skill_rows: Sequence[Dict[str, str]],
    kb_entries: Sequence[Dict[str, str]],
) -> Dict[str, object]:
    reasons: List[str] = []
    actions: List[str] = []
    score = 0

    status_hint = metrics.get("status", "")
    if "no rows found" in status_hint:
        return {
            "skill": skill,
            "status": "no_data",
            "score": 0,
            "reasons": ["No rows found for this skill in selected range."],
            "suggested_actions": ["Run more tasks with this skill before evaluating optimization."],
            "metrics": metrics,
            "top_root_causes": [],
            "sample_size_skill": 0,
            "can_trigger": True,
        }

    if "insufficient baseline" in status_hint:
        score += 50
        reasons.append("Insufficient baseline on matching task types.")
        actions.append("Collect at least 10 no-skill baseline samples on the same task types.")

    sample_size_skill = _parse_int(metrics.get("sample_size_skill", ""))
    if sample_size_skill is not None and sample_size_skill < 10:
        score += 10
        reasons.append(f"Skill sample size is low ({sample_size_skill}).")
        actions.append("Increase sample size before finalizing optimization decisions.")

    token_reduction = _parse_percent(metrics.get("token_reduction_pct", ""))
    if token_reduction is not None and token_reduction < 0:
        score += 35
        reasons.append(f"Token cost is worse than baseline ({metrics.get('token_reduction_pct')}).")
        actions.append("Tighten trigger guidance and reduce prompt context for this skill.")

    duration_reduction = _parse_percent(metrics.get("duration_reduction_pct", ""))
    if duration_reduction is not None and duration_reduction < 0:
        score += 20
        reasons.append(f"Duration is worse than baseline ({metrics.get('duration_reduction_pct')}).")
        actions.append("Move repeated logic into deterministic scripts to reduce cycle time.")

    success_delta = _parse_pp(metrics.get("success_rate_delta_pp", ""))
    if success_delta is not None and success_delta < 0:
        score += 35
        reasons.append(f"Success rate regressed ({metrics.get('success_rate_delta_pp')}).")
        actions.append("Add stricter validation gates and done criteria to this skill workflow.")

    rework_delta = _parse_float(metrics.get("rework_rate_delta", ""))
    if rework_delta is not None and rework_delta > 0:
        score += 30
        reasons.append(f"Rework rate increased ({metrics.get('rework_rate_delta')}).")
        actions.append("Add rollback-safe checkpoints and earlier failure signals in the workflow.")

    top_root_causes = _top_root_causes_for_skill(skill_rows, kb_entries)
    if top_root_causes:
        actions.append("Address top recurring root causes first when rewriting SKILL.md and scripts.")

    if score >= 70:
        status = "needs_optimization"
    elif score >= 35:
        status = "watch"
    else:
        status = "healthy"
        if not reasons:
            reasons.append("No major regression signal detected in selected range.")
            actions.append("Keep current design and continue monitoring weekly.")

    return {
        "skill": skill,
        "status": status,
        "score": score,
        "reasons": _unique_ordered(reasons),
        "suggested_actions": _unique_ordered(actions),
        "metrics": metrics,
        "top_root_causes": top_root_causes,
        "sample_size_skill": sample_size_skill if sample_size_skill is not None else "n/a",
        "can_trigger": True,
    }


def discover_skill_opportunities(
    paths: RuntimePaths,
    filtered_data_file: Path,
    filtered_rows: Sequence[Dict[str, str]],
    start: str,
    end: str,
    cutover: str,
) -> List[Dict[str, object]]:
    skills = collect_skills(filtered_rows)
    if not skills:
        return []

    kb_entries = load_kb_entries(paths.kb_dir, start, end)
    opportunities: List[Dict[str, object]] = []
    for skill in skills:
        cmd = [str(paths.metrics_script), "--skill", skill]
        if cutover:
            cmd.extend(["--cutover", cutover])
        raw_output = run_script(cmd, {"AOSO_DATA_FILE": str(filtered_data_file)})
        sections = parse_metrics_output(raw_output)
        metrics = _find_skill_metrics(sections, skill)
        skill_rows = [
            row
            for row in filtered_rows
            if row.get("used_skill", "").strip().lower() == "true"
            and row.get("skill_name", "").strip() == skill
        ]
        item = build_skill_opportunity(skill, metrics, skill_rows, kb_entries)
        item["raw_output"] = raw_output
        opportunities.append(item)

    opportunities.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
    return opportunities


def parse_key_value_from_output(output: str, key: str) -> str:
    prefix = f"{key}: "
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.replace(prefix, "", 1).strip()
    return ""


def run_weekly_review(
    paths: RuntimePaths, start: str, end: str
) -> str:
    if not paths.kb_dir.exists():
        return "knowledge-base/errors directory not found."

    with tempfile.TemporaryDirectory(prefix="aoso-dashboard-weekly-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        tmp_kb = tmp_root / "kb"
        tmp_report = tmp_root / "reports"
        tmp_kb.mkdir(parents=True, exist_ok=True)
        tmp_report.mkdir(parents=True, exist_ok=True)

        for md in paths.kb_dir.glob("*.md"):
            entry_date = ""
            try:
                with md.open("r", encoding="utf-8") as fp:
                    for raw in fp:
                        if raw.startswith("date: "):
                            entry_date = raw.replace("date: ", "", 1).strip()
                            break
            except UnicodeDecodeError:
                continue
            if not _is_date(entry_date):
                continue
            if start and entry_date < start:
                continue
            if end and entry_date > end:
                continue
            shutil.copy2(md, tmp_kb / md.name)

        output = run_script(
            [str(paths.weekly_script)],
            {
                "AOSO_KB_DIR": str(tmp_kb),
                "AOSO_REPORT_DIR": str(tmp_report),
            },
        )

        report_file = None
        for line in output.splitlines():
            if line.startswith("generated report: "):
                report_file = line.replace("generated report: ", "", 1).strip()
                break
        if not report_file:
            return output
        path = Path(report_file)
        if not path.exists():
            return output
        return path.read_text(encoding="utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    runtime_paths: RuntimePaths

    def _json(self, payload: Dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _text(self, text: str, status: int = 200, mime: str = "text/plain") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _bad_request(self, message: str) -> None:
        self._json({"error": message}, status=HTTPStatus.BAD_REQUEST)

    def _validate_filters(
        self, start: str, end: str, cutover: str
    ) -> str:
        if start and not _is_date(start):
            return "invalid start date, expected YYYY-MM-DD"
        if end and not _is_date(end):
            return "invalid end date, expected YYYY-MM-DD"
        if cutover and not _is_date(cutover):
            return "invalid cutover date, expected YYYY-MM-DD"
        if start and end and start > end:
            return "start date must be <= end date"
        return ""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self._text(HTML_PAGE, mime="text/html")
            return
        if path == "/api/options":
            self.handle_options()
            return
        if path == "/api/report":
            self.handle_report(query)
            return
        if path == "/api/opportunities":
            self.handle_opportunities(query)
            return
        self._bad_request(f"unknown endpoint: {path}")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/optimize":
            self.handle_optimize()
            return
        self._bad_request(f"unknown endpoint: {parsed.path}")

    def handle_options(self) -> None:
        fieldnames, rows = read_task_rows(self.runtime_paths.data_file)
        dates = sorted(
            {
                row.get("date", "")
                for row in rows
                if row.get("date") and _is_date(row.get("date", ""))
            }
        )
        if dates:
            default_start = dates[0]
            default_end = dates[-1]
        else:
            today = _today()
            default_start = today
            default_end = today

        payload = {
            "fields": fieldnames,
            "skills": collect_skills(rows),
            "default_start": default_start,
            "default_end": default_end,
            "default_cutover": default_start,
            "data_file": str(self.runtime_paths.data_file),
        }
        self._json(payload)

    def handle_report(self, query: Dict[str, List[str]]) -> None:
        start = query.get("start", [""])[0]
        end = query.get("end", [""])[0]
        cutover = query.get("cutover", [""])[0]
        skill = query.get("skill", [""])[0].strip()

        validation_error = self._validate_filters(start, end, cutover)
        if validation_error:
            self._bad_request(validation_error)
            return

        fieldnames, rows = read_task_rows(self.runtime_paths.data_file)
        if not fieldnames:
            self._json(
                {
                    "row_count": 0,
                    "sections": [],
                    "flat_metrics": {},
                    "opportunities": [],
                    "new_skill_recommendations": [],
                    "overall_raw": "No data file found or no header row.",
                    "skill_raw": "",
                    "weekly_raw": "",
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "data_file": str(self.runtime_paths.data_file),
                }
            )
            return

        filtered_rows = filter_rows(rows, start, end)

        with tempfile.TemporaryDirectory(prefix="aoso-dashboard-") as tmp_dir:
            tmp_csv = Path(tmp_dir) / "filtered.csv"
            write_filtered_csv(fieldnames, filtered_rows, tmp_csv)
            kb_entries = load_kb_entries(self.runtime_paths.kb_dir, start, end)

            metrics_cmd: List[str] = [str(self.runtime_paths.metrics_script), "--all"]
            if cutover:
                metrics_cmd.extend(["--cutover", cutover])
            overall_raw = run_script(metrics_cmd, {"AOSO_DATA_FILE": str(tmp_csv)})

            skill_raw = ""
            if skill:
                skill_cmd: List[str] = [
                    str(self.runtime_paths.metrics_script),
                    "--skill",
                    skill,
                ]
                if cutover:
                    skill_cmd.extend(["--cutover", cutover])
                skill_raw = run_script(skill_cmd, {"AOSO_DATA_FILE": str(tmp_csv)})

            weekly_raw = run_weekly_review(self.runtime_paths, start, end)
            opportunities = discover_skill_opportunities(
                self.runtime_paths,
                tmp_csv,
                filtered_rows,
                start,
                end,
                cutover,
            )
            new_skill_recommendations = discover_new_skill_recommendations(
                filtered_rows,
                kb_entries,
            )

        sections = parse_metrics_output("\n".join([overall_raw, skill_raw]).strip())
        payload = {
            "row_count": len(filtered_rows),
            "sections": sections,
            "flat_metrics": flatten_metrics(sections),
            "opportunities": opportunities,
            "new_skill_recommendations": new_skill_recommendations,
            "overall_raw": overall_raw,
            "skill_raw": skill_raw,
            "weekly_raw": weekly_raw,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "data_file": str(self.runtime_paths.data_file),
        }
        self._json(payload)

    def handle_opportunities(self, query: Dict[str, List[str]]) -> None:
        start = query.get("start", [""])[0]
        end = query.get("end", [""])[0]
        cutover = query.get("cutover", [""])[0]
        validation_error = self._validate_filters(start, end, cutover)
        if validation_error:
            self._bad_request(validation_error)
            return

        fieldnames, rows = read_task_rows(self.runtime_paths.data_file)
        if not fieldnames:
            self._json({"opportunities": [], "row_count": 0})
            return

        filtered_rows = filter_rows(rows, start, end)
        with tempfile.TemporaryDirectory(prefix="aoso-dashboard-op-") as tmp_dir:
            tmp_csv = Path(tmp_dir) / "filtered.csv"
            write_filtered_csv(fieldnames, filtered_rows, tmp_csv)
            opportunities = discover_skill_opportunities(
                self.runtime_paths,
                tmp_csv,
                filtered_rows,
                start,
                end,
                cutover,
            )
        self._json({"opportunities": opportunities, "row_count": len(filtered_rows)})

    def handle_optimize(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._bad_request("invalid Content-Length")
            return

        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._bad_request("invalid JSON body")
            return
        if not isinstance(payload, dict):
            self._bad_request("request body must be an object")
            return

        skill = str(payload.get("skill", "")).strip()
        start = str(payload.get("start", "")).strip()
        end = str(payload.get("end", "")).strip()
        cutover = str(payload.get("cutover", "")).strip()
        if not skill:
            self._bad_request("field `skill` is required")
            return

        validation_error = self._validate_filters(start, end, cutover)
        if validation_error:
            self._bad_request(validation_error)
            return

        cmd: List[str] = [str(self.runtime_paths.optimize_script), "--skill", skill]
        if start:
            cmd.extend(["--start", start])
        if end:
            cmd.extend(["--end", end])
        if cutover:
            cmd.extend(["--cutover", cutover])

        try:
            output = run_script(cmd, {})
        except RuntimeError as exc:
            self._bad_request(str(exc))
            return
        self._json(
            {
                "skill": skill,
                "report_file": parse_key_value_from_output(output, "generated optimization report"),
                "optimization_status": parse_key_value_from_output(output, "optimization_status"),
                "opportunity_score": parse_key_value_from_output(output, "opportunity_score"),
                "raw_output": output,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local web dashboard for self-optimizing loop."
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host")
    parser.add_argument("--port", type=int, default=8765, help="bind port")
    args = parser.parse_args()

    paths = resolve_runtime_paths()
    if not paths.metrics_script.exists():
        raise SystemExit(f"missing script: {paths.metrics_script}")
    if not paths.weekly_script.exists():
        raise SystemExit(f"missing script: {paths.weekly_script}")
    if not paths.optimize_script.exists():
        raise SystemExit(f"missing script: {paths.optimize_script}")

    handler = DashboardHandler
    handler.runtime_paths = paths
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        print(f"dashboard server listening on http://{args.host}:{args.port}")
        print(f"data_file={paths.data_file}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
