from __future__ import annotations

import os
import re
import shlex
from threading import Thread
from urllib.parse import urlparse
from typing import Optional, Tuple, List

import tkinter as tk
from tkinter import (
    Toplevel, Label, Entry, Button, BOTH, RIGHT, Y,
    filedialog, messagebox, simpledialog
)

# GitPython availability
try:
    from git import Repo, Git, GitCommandError  # type: ignore
    _GIT_AVAILABLE = True
except Exception:
    Repo = None  # type: ignore
    Git = None   # type: ignore
    GitCommandError = Exception  # type: ignore
    _GIT_AVAILABLE = False


# ---------------- Safety helpers ----------------

def _is_git_available() -> bool:
    return _GIT_AVAILABLE and Repo is not None  # type: ignore[truthy-function]


def _find_repo_root(path: str) -> Optional[str]:
    '''
    Return the repo root containing a .git directory, or None.
    Accepts a file or directory path and walks upward.
    '''
    try:
        from pathlib import Path
        p = Path(path)
        if p.is_file():
            p = p.parent
        for cur in [p, *p.parents]:
            if (cur / '.git').exists():
                return str(cur)
    except Exception:
        pass
    return None


def _validate_repo_path_or_warn(app, path: str) -> Optional[str]:
    root = _find_repo_root(path)
    if not root:
        try:
            messagebox.showerror(app.title_struct + 'git', 'Selected folder is not a valid Git repository.')
        except Exception:
            pass
        return None
    return root


def _validate_clone_url_or_warn(app, link: str) -> Optional[str]:
    '''Block dangerous URLs (embedded creds) and allow only safe schemes.'''
    try:
        parsed = urlparse(link)
        safe_schemes = {'https', 'ssh', 'git', 'file'}
        if parsed.scheme.lower() not in safe_schemes:
            messagebox.showerror(app.title_struct + 'git', f'Unsupported URL scheme: {parsed.scheme}')
            return None
        if parsed.username or parsed.password:
            messagebox.showerror(app.title_struct + 'git', 'Credentials in URL are not allowed.')
            return None
        return link
    except Exception:
        messagebox.showerror(app.title_struct + 'git', 'Invalid repository URL.')
        return None


_SAFE_EXEC_ALLOWLIST = {
    # Read-only, safe-ish subcommands
    'status', 'log', 'branch', 'rev-parse', 'show', 'diff', 'ls-files', 'remote', 'describe'
}


def _run_long_task(app, title: str, fn):
    '''Run a long Git task in a thread with minimal status feedback.'''
    try:
        notice = Toplevel()
        if hasattr(app, 'make_tm'):
            app.make_tm(notice)
        notice.title(getattr(app, 'title_struct', '') + title)
        Label(notice, text=f'{title} in progress...', font='arial 10').pack(padx=10, pady=8)
        try:
            owner = getattr(app, 'root', None) or getattr(app, 'master', None)
            if isinstance(owner, tk.Misc):
                notice.transient(owner)
        except Exception:
            pass
        notice.update_idletasks()
    except Exception:
        notice = None

    def _runner():
        err = None
        try:
            fn()
        except Exception as e:
            err = e
        finally:
            try:
                if notice and notice.winfo_exists():
                    notice.destroy()
            except Exception:
                pass
            if err:
                try:
                    messagebox.showerror(getattr(app, 'title_struct', '') + ' git', str(err))
                except Exception:
                    pass
            else:
                try:
                    messagebox.showinfo(getattr(app, 'title_struct', '') + ' git', f'{title} completed')
                except Exception:
                    pass

    Thread(target=_runner, daemon=True).start()


def _redact_pii(text: str) -> str:
    '''Redact emails to reduce accidental PII exposure.'''
    try:
        return re.sub(r'([A-Za-z0-9._%+-]{1,})@([A-Za-z0-9.-]{1,}\.[A-Za-z]{2,})', '[redacted@email]', text or '')
    except Exception:
        return text


def _get_staged_files(repo: 'Repo') -> List[str]:
    '''Return list of staged file paths relative to repo root.'''
    try:
        out = repo.git.diff('--name-only', '--cached')
        return [p for p in out.splitlines() if p.strip()]
    except Exception:
        return []


def _scan_for_secrets_and_large(app, repo: 'Repo', rel_paths: List[str], max_bytes: int = 10 * 1024 * 1024) -> Tuple[List[str], List[Tuple[str, int]]]:
    '''
    Scan staged files for likely secrets and large files.
    Returns (secret_hits, large_files).
    '''
    secret_hits: List[str] = []
    big_files: List[Tuple[str, int]] = []
    patterns = [
        re.compile(r'-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'),
        re.compile(r'AKIA[0-9A-Z]{16}'),
        re.compile(r'(?i)secret[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9/+]{12,}[\'"]'),
        re.compile(r'(?i)api[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9_\-]{12,}[\'"]'),
        re.compile(r'(?i)password\s*[:=]\s*[\'"].{4,}[\'"]'),
        re.compile(r'ghp_[A-Za-z0-9]{36,}'),
    ]
    repo_root = repo.working_tree_dir or ''
    for rel in rel_paths:
        abs_p = os.path.join(repo_root, rel)
        try:
            size = os.path.getsize(abs_p)
            if size >= max_bytes:
                big_files.append((rel, size))
            with open(abs_p, 'rb') as f:
                chunk = f.read(512 * 1024)  # up to 512KB
            try:
                text = chunk.decode('utf-8', errors='ignore')
            except Exception:
                text = ''
            if text:
                for pat in patterns:
                    if pat.search(text):
                        secret_hits.append(rel)
                        break
        except Exception:
            continue
    return secret_hits, big_files


# ---------------- Public entry ----------------

def open_git_tool(app, action: str):
    '''
    Git tool entry point (popup-oriented), using app context for UI helpers.
    Safety-first: validations, confirmations, allowlist for execute, non-blocking clone/pull,
    secret/large-file scans before commit, and PII redaction in outputs.
    '''
    if not _is_git_available():
        messagebox.showerror(getattr(app, 'title_struct', '') + 'git',
                             'Git features are unavailable (GitPython not installed).')
        return

    git_ui = False
    title = None
    git_text = None
    text_frame = text_scroll = None

    if action in ('repo info', 'commit data'):
        git_ui = True
        git_root = Toplevel()
        if hasattr(app, 'make_tm'):
            app.make_tm(git_root)
        git_root.title(getattr(app, 'title_struct', '') + 'Git window')
        title = Label(git_root, text='', font='arial 14 bold')
        title.pack()
        if hasattr(app, 'make_rich_textbox'):
            (text_frame, git_text, text_scroll) = app.make_rich_textbox(git_root, place=False)
            text_frame.pack(fill=BOTH, expand=True)
            text_scroll.pack(side=RIGHT, fill=Y)
            git_text.pack(fill=BOTH, expand=True)

    # Open repo for all actions except 'clone'
    repo = None
    repo_path = None
    if action != 'clone':
        selection = filedialog.askdirectory(title='Open repository folder')
        if not selection:
            messagebox.showerror('EgonTE', 'No repository selected')
            return
        repo_path = _validate_repo_path_or_warn(app, selection)
        if not repo_path:
            return
        try:
            repo = Repo(repo_path)  # type: ignore
        except Exception as e:
            messagebox.showerror('EgonTE', f'Failed to open the repository:\n{e}')
            return

    # Actions needing repo
    if repo:
        if action == 'repo info':
            if title:
                title.configure(text='Repository information')
            try:
                status = repo.git.status()
            except Exception:
                status = '(failed to get status)'

            repo_description = getattr(repo, 'description', '') or '(no description)'
            try:
                active_branch = repo.active_branch
            except Exception:
                active_branch = '(detached HEAD or unknown)'

            if git_text is not None:
                git_text.insert('1.0',
                                f'Status:\n{status}\nDescription:\n{repo_description}\nActive branch:\n{active_branch}\nRemotes:\n')

            remote_dict = {}
            try:
                for remote in repo.remotes:
                    try:
                        urls = list(remote.urls)
                        remote_dict[remote] = ', '.join(urls) if urls else '(no url)'
                    except Exception:
                        remote_dict[remote] = getattr(remote, 'url', '(no url)')
            except Exception:
                pass

            if git_text is not None:
                for remote, url in remote_dict.items():
                    git_text.insert('end', f'{remote} - {url}\n')

                try:
                    last_commit = str(repo.head.commit.hexsha)
                except Exception:
                    last_commit = '(no commits)'

                git_text.insert('end', f'\nLast commit:\n{last_commit}')

        elif action == 'execute':
            command = simpledialog.askstring('Git', 'Enter git subcommand (safe subset)\nAllowed: '
                                           + ', '.join(sorted(_SAFE_EXEC_ALLOWLIST)))
            if command:
                try:
                    parts = shlex.split(command)
                    if not parts:
                        return
                    sub = parts[0]
                    if sub not in _SAFE_EXEC_ALLOWLIST:
                        messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'Command not allowed: {sub}')
                        return
                    output = repo.git.execute(['git', *parts])
                    output = _redact_pii(output)
                    if git_ui and git_text is not None:
                        git_text.insert('end', f'\n$ git {command}\n{output}\n')
                    else:
                        messagebox.showinfo(getattr(app, 'title_struct', '') + ' git', 'Command executed successfully')
                except Exception as e:
                    messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'Command failed:\n{e}')

        elif action == 'pull':
            # Require clean tree or stash
            try:
                is_dirty = repo.is_dirty(untracked_files=True)
            except Exception:
                is_dirty = False

            if is_dirty:
                try:
                    choice = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git',
                                                 'Uncommitted changes detected.\nStash changes before pulling?')
                except Exception:
                    choice = False
                if not choice:
                    return
                try:
                    repo.git.stash('push', '-u', '-m', 'EgonTE auto-stash before pull')
                except Exception as e:
                    messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'Failed to stash changes:\n{e}')
                    return

            try:
                ok = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git', 'Pull latest changes from remote?')
            except Exception:
                ok = True
            if not ok:
                return

            def _do_pull():
                repo.git.pull()

            _run_long_task(app, 'Pull', _do_pull)

        elif action == 'add':
            try:
                ok = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git', 'Stage ALL changes (git add --all)?')
            except Exception:
                ok = True
            if not ok:
                return
            try:
                repo.git.add('--all')
                messagebox.showinfo(getattr(app, 'title_struct', '') + ' git', 'Staged all changes')
            except Exception as e:
                messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'Add failed:\n{e}')

        elif action == 'commit':
            def commit_enter():
                try:
                    message, author_ = message_entry.get().strip(), author_entry.get().strip()

                    staged = _get_staged_files(repo)  # type: ignore
                    if not staged:
                        messagebox.showerror(getattr(app, 'title_struct', '') + ' git', 'No staged changes to commit.')
                        return

                    secret_hits, big_files = _scan_for_secrets_and_large(app, repo, staged)  # type: ignore
                    if secret_hits or big_files:
                        warn_lines = []
                        if secret_hits:
                            warn_lines.append('Potential secrets detected in:\n  - ' + '\n  - '.join(secret_hits))
                        if big_files:
                            warn_lines.append('Large files staged (>=10MB):\n  - ' + '\n  - '.join(
                                f'{p} ({sz/1024/1024:.1f} MB)' for p, sz in big_files))
                        warn_msg = '\n\n'.join(warn_lines) + '\n\nProceed with commit?'
                        try:
                            allow = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git', warn_msg)
                        except Exception:
                            allow = False
                        if not allow:
                            return

                    if not message:
                        try:
                            allow = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git',
                                                        'Empty commit message. Continue anyway?')
                        except Exception:
                            allow = False
                        if not allow:
                            return
                        message = 'Update via EgonTE'

                    args = ['-m', message]
                    if author_:
                        args.append(f'--author={author_}')
                    repo.git.commit(*args)
                    commit_window.destroy()
                    messagebox.showinfo(getattr(app, 'title_struct', '') + ' git', 'Commit completed')
                except Exception as e:
                    messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'An error has occurred:\n{e}')

            commit_window = Toplevel()
            if hasattr(app, 'make_tm'):
                app.make_tm(commit_window)
            commit_window.title(getattr(app, 'title_struct', '') + 'Git commit')
            message_title = Label(commit_window, text='Message:', font='arial 10 underline')
            message_entry = Entry(commit_window, width=50)
            author_title = Label(commit_window, text='Author (Name <email>):', font='arial 10 underline')
            author_entry = Entry(commit_window, width=50)
            enter = Button(commit_window, text='Commit', command=commit_enter)

            for widget in (message_title, message_entry, author_title, author_entry, enter):
                widget.pack(padx=6, pady=3)

    # Actions that don't need an opened repo
    if action == 'clone':
        link = simpledialog.askstring('EgonTE', 'Please enter the repository link')
        if not link:
            return
        link = _validate_clone_url_or_warn(app, link)
        if not link:
            return

        target_dir = filedialog.askdirectory(title='Choose empty folder to clone into')
        if not target_dir:
            return
        try:
            if os.path.exists(target_dir) and os.listdir(target_dir):
                try:
                    ok = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git',
                                             'Target folder is not empty. Clone anyway?')
                except Exception:
                    ok = False
                if not ok:
                    return
        except Exception:
            pass

        def _do_clone():
            Repo.clone_from(link, target_dir)  # type: ignore

        _run_long_task(app, 'Clone', _do_clone)

    elif action == 'commit data' and repo:
        if title:
            title.configure(text='Commit data')
        try:
            commit_obj = repo.head.commit  # type: ignore
            commit_hash = str(commit_obj.hexsha)
            author_str = f'{commit_obj.author.name} ({commit_obj.author.email})'
            author_str = _redact_pii(author_str)
            by = f'"{commit_obj.summary}" by {author_str}'
            date_time = str(commit_obj.authored_datetime)
            count_size = f'count: {len(str(commit_obj))} and size: {commit_obj.size}'
        except Exception as e:
            commit_hash, by, date_time, count_size = '(n/a)', f'(n/a)\n{e}', '(n/a)', '(n/a)'

        if git_text is not None:
            git_text.insert('1.0',
                            f'Commit:\n{commit_hash}\nSummary & author:\n{by}\nDate/time:\n{date_time}\nCount & size:\n{count_size}')

        def commit_enter():
            try:
                message, author_ = message_entry.get().strip(), author_entry.get().strip()

                staged = _get_staged_files(repo)  # type: ignore
                if not staged:
                    messagebox.showerror(getattr(app, 'title_struct', '') + ' git', 'No staged changes to commit.')
                    return

                secret_hits, big_files = _scan_for_secrets_and_large(app, repo, staged)  # type: ignore
                if secret_hits or big_files:
                    warn_lines = []
                    if secret_hits:
                        warn_lines.append('Potential secrets detected in:\n  - ' + '\n  - '.join(secret_hits))
                    if big_files:
                        warn_lines.append('Large files staged (>=10MB):\n  - ' + '\n  - '.join(
                            f'{p} ({sz/1024/1024:.1f} MB)' for p, sz in big_files))
                    warn_msg = '\n\n'.join(warn_lines) + '\n\nProceed with commit?'
                    try:
                        allow = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git', warn_msg)
                    except Exception:
                        allow = False
                    if not allow:
                        return

                if not message:
                    try:
                        allow = messagebox.askyesno(getattr(app, 'title_struct', '') + ' git',
                                                    'Empty commit message. Continue anyway?')
                    except Exception:
                        allow = False
                    if not allow:
                        return
                    message = 'Update via EgonTE'

                args = ['-m', message]
                if author_:
                    args.append(f'--author={author_}')
                repo.git.commit(*args)
                commit_window.destroy()
                messagebox.showinfo(getattr(app, 'title_struct', '') + ' git', 'Commit completed')
            except Exception as e:
                messagebox.showerror(getattr(app, 'title_struct', '') + ' git', f'An error has occurred:\n{e}')

        commit_window = Toplevel()
        if hasattr(app, 'make_tm'):
            app.make_tm(commit_window)
        commit_window.title(getattr(app, 'title_struct', '') + 'Git commit window')
        message_title = Label(commit_window, text='Message:', font='arial 10 underline')
        message_entry = Entry(commit_window)
        author_title = Label(commit_window, text='Author:', font='arial 10 underline')
        author_entry = Entry(commit_window)
        enter = Button(commit_window, text='Commit', command=commit_enter)

        for widget in (message_title, message_entry, author_title, author_entry, enter):
            widget.pack(pady=1)
