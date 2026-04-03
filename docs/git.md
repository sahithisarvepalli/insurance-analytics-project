# 🐙 Git & Dev Container Tips

> **Concept:** Git tracks changes to your code. Sometimes the Dev Container environment (Linux inside Docker) sees files differently than your host machine (Windows/Mac), which causes Git to show false changes.

---

## 🔍 Problem: All Files Show as "Changed" in Dev Container

This is usually caused by **line ending differences** (Windows uses `CRLF`, Linux uses `LF`) or **file permission** differences between your host OS and the container.

```
Host (Windows/Mac)           Dev Container (Linux)
   CRLF line endings    ≠       LF line endings
   chmod 755 files      ≠       chmod 644 files
         ↓
   Git sees everything as "modified" even though content is the same
```

---

## 🛠️ Fix It

**Step 1 — Check what Git sees:**
```bash
git status
```

**Step 2 — Fix line endings:**
```bash
git config --global core.autocrlf input
git reset --hard HEAD
```

**Step 3 — Fix file permission noise (if still showing changes):**
```bash
git config core.fileMode false
git reset --hard HEAD
```

**Step 4 — Sync with remote:**
```bash
git fetch && git pull
```

---

## 🛡️ Prevent It Permanently

Add a `.gitattributes` file at the repo root:

```
* text=auto eol=lf
```

This auto-detects text files and enforces Linux-style line endings everywhere, regardless of the contributor's OS.

---

## 💾 Committing from Inside the Dev Container

```bash
git add .
git commit -m "your message"
git push
```

Or use the **VS Code Source Control panel** (left sidebar `⎇` icon) — works the same inside the container.

---

## ✅ Verify Your Setup

```bash
git rev-parse --show-toplevel   # confirm you're at the repo root
git log --oneline -5            # see recent commits
```
