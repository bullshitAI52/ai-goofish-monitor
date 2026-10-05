import importlib


def _load_scraper(monkeypatch, *, login_is_edge: bool, running_in_docker: bool):
    monkeypatch.setenv("LOGIN_IS_EDGE", "true" if login_is_edge else "false")
    monkeypatch.setenv("RUNNING_IN_DOCKER", "true" if running_in_docker else "false")

    import src.config as config_module
    import src.scraper as scraper_module

    importlib.reload(config_module)
    reloaded_scraper = importlib.reload(scraper_module)
    reloaded_scraper.EDGE_DOCKER_WARNING_PRINTED = False
    return reloaded_scraper


def test_resolve_browser_channel_uses_chromium_in_docker_even_when_edge_requested(monkeypatch, capsys):
    scraper = _load_scraper(monkeypatch, login_is_edge=True, running_in_docker=True)

    assert scraper._resolve_browser_channel() == "chromium"
    assert "Docker 镜像未内置 Edge" in capsys.readouterr().out


def test_resolve_browser_channel_uses_msedge_locally_when_requested(monkeypatch):
    scraper = _load_scraper(monkeypatch, login_is_edge=True, running_in_docker=False)

    assert scraper._resolve_browser_channel() == "msedge"


def test_resolve_browser_channel_uses_bundled_chromium_locally(monkeypatch):
    scraper = _load_scraper(monkeypatch, login_is_edge=False, running_in_docker=False)
    assert scraper._resolve_browser_channel() == "chromium"


def test_snapshot_headers_do_not_override_browser_metadata(monkeypatch):
    scraper = _load_scraper(monkeypatch, login_is_edge=False, running_in_docker=False)
    raw = {
        "Sec-Fetch-Site": "same-origin", "sec-fetch-dest": "empty",
        "Sec-CH-UA-Mobile": "?0", "sec-ch-ua": "old browser",
        "Referer": "https://example.com", "Accept-Encoding": "gzip",
        "Accept": "*/*", "Content-Type": "application/json",
        "Content-Length": "10", "Cookie": "secret", "Origin": "https://example.com",
        "User-Agent": "old browser", "Host": "example.com", "Connection": "keep-alive",
        "X-Custom-Header": "keep", "Accept-Language": "zh-CN", "X-Empty": None,
    }
    assert scraper._build_extra_headers(raw) == {
        "X-Custom-Header": "keep", "Accept-Language": "zh-CN",
    }
    assert raw["Cookie"] == "secret"
    assert scraper._build_extra_headers(None) == {}
