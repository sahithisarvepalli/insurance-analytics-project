## Troubleshooting

### Git shows all files as changed inside Dev Container

When opening the project in a **VS Code Dev Container**, you may see many files appear in the **Source Control "Changes" section**, even though those files are already committed in GitHub.

This usually happens because the container environment handles **line endings or file permissions differently** than the host system.

---

### 1. Check Git status inside the container

Open a terminal in the Dev Container and run:

```bash
git status
```

This will show what Git inside the container believes has changed.

---

### 2. Fix line ending issues

If your host machine uses different line endings (e.g., Windows CRLF vs Linux LF), Git may mark all files as modified.

Run:

```bash
git config --global core.autocrlf input
```

Then reset the repository state:

```bash
git reset --hard HEAD
```

---

### 3. Fix file permission differences

Linux containers sometimes change executable file permissions, causing Git to detect changes.

Check the current setting:

```bash
git config core.fileMode
```

If it returns `true`, disable it:

```bash
git config core.fileMode false
```

Then reset again:

```bash
git reset --hard HEAD
```

---

### 4. Synchronize with the remote repository

Ensure the container has the latest commits:

```bash
git fetch
git pull
```

---

### 5. Verify the repository root

Ensure the container is opened at the correct repository root:

```bash
git rev-parse --show-toplevel
```

---

### 6. Commit changes from the Dev Container

After resolving the issues, you can commit and push changes directly from the Dev Container:

```bash
git add .
git commit -m "your message"
git push
```

You can also use the **VS Code Source Control panel** inside the Dev Container to commit and push changes.

---

### 7. Prevent future line ending issues

Add a `.gitattributes` file in the repository root:

```text
* text=auto
```

Or enforce Linux-style line endings:

```text
* text eol=lf
```

This ensures consistent line endings across different environments.
