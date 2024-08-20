# TODOs and bug tracking
- [x] fix all commands executing themselves twice
  - status: Identifying the issue
  - Notes
    - It appears that it is executing the entire `main()` function within `main.py` twice, per the log.
    - Issue found: `main()` is being called twice due to `cmusic.py` executing it when imported.
    - Issue fixed, `main()` is now only called when `__name__ == '__main__'`
- [ ] fix using `cmusic play <song> --loop` and then `cmusic queue <song>` causing only the latest queued song to loop