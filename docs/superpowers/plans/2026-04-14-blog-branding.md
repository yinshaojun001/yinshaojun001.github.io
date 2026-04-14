# Blog Branding Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a clean author info card to the About page and further polish the homepage into a restrained author-branded presentation.

**Architecture:** Keep the current Hugo structure and content model intact. Modify only the About content/template path and the homepage content/template/styles so the brand expression becomes clearer without changing route structure or deployment behavior.

**Tech Stack:** Hugo, Markdown, Hugo templates, CSS

---

### Task 1: Add the About author info card

**Files:**
- Modify: `content/about/_index.md`
- Modify: `layouts/_default/list.html`
- Modify: `assets/css/main.css`

- [ ] Add structured About card fields (name, role, city, GitHub, email, WeChat/public account, focus tags)
- [ ] Update the list template to render the About card only on the About page
- [ ] Add restrained styling for the About card
- [ ] Run `hugo --destination /tmp/yinshaojun001-about-branding`
- [ ] Verify the About page contains the contact info and focus tags
- [ ] Commit with `git commit -m "feat: add about author info card"`

---

### Task 2: Upgrade homepage to the approved author-brand direction

**Files:**
- Modify: `content/_index.md`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`

- [ ] Refine homepage copy to better express identity and writing direction
- [ ] Upgrade hero / author card / topic entrance layout without making it visually heavy
- [ ] Improve homepage card styling and spacing
- [ ] Run `hugo --destination /tmp/yinshaojun001-home-branding`
- [ ] Verify homepage contains the refined identity messaging and latest-posts section
- [ ] Commit with `git commit -m "feat: refine homepage author branding"`

---

### Task 3: Final verification

**Files:**
- No required file changes unless small cleanup is needed

- [ ] Run `hugo --minify --destination /tmp/yinshaojun001-branding-final`
- [ ] Verify `/`, `/about/`, `/posts/`, `/tags/`
- [ ] Commit any final cleanup if needed

---

## References

- Spec: `docs/superpowers/specs/2026-04-14-blog-branding-design.md`
