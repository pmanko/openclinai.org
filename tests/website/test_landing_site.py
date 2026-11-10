from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[2]
LANDING = ROOT / "landing"


class LandingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.videos: list[dict[str, str | None]] = []
        self.sources: list[str] = []
        self.h1_count = 0
        self.scripts: list[dict[str, str | None]] = []
        self.assets: list[str] = []
        self.meta_images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "img":
            self.images.append(values)
            if values.get("srcset"):
                for candidate in str(values["srcset"]).split(","):
                    tokens = candidate.strip().split()
                    if tokens:
                        self.assets.append(tokens[0])
        elif tag == "video":
            self.videos.append(values)
        elif tag == "source":
            if values.get("src"):
                self.sources.append(str(values["src"]))
            if values.get("srcset"):
                for candidate in str(values["srcset"]).split(","):
                    tokens = candidate.strip().split()
                    if tokens:
                        self.assets.append(tokens[0])
        elif tag == "meta" and values.get("property") == "og:image" and values.get("content"):
            content = str(values["content"])
            self.meta_images.append(content)
            if content.startswith("https://openclinai.org/"):
                self.assets.append(content.removeprefix("https://openclinai.org"))
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "script":
            self.scripts.append(values)
        elif tag == "link" and values.get("href"):
            self.assets.append(str(values["href"]))


def parsed_landing() -> tuple[str, LandingParser]:
    html = (LANDING / "index.html").read_text(encoding="utf-8")
    parser = LandingParser()
    parser.feed(html)
    return html, parser


def local_asset(path: str) -> Path:
    return LANDING / path.removeprefix("/")


MEDIA_HOST = "https://storage.googleapis.com/openclinai-media/"
DEMO_HOSTS = ("catalyst.openelis-global.org", "openmrs.openclinai.org", "pmanko.github.io")


def parsed_page(relative_path):
    html = (LANDING / relative_path).read_text(encoding="utf-8")
    page = LandingParser()
    page.feed(html)
    return html, page


def pages():
    for path in sorted(LANDING.rglob("*.html")):
        html, page = parsed_page(path.relative_to(LANDING))
        yield path, page


def resolve(path: Path, reference: str) -> Path:
    target = urlparse(reference).path
    if not target:
        return path
    destination = LANDING / target.lstrip("/") if target.startswith("/") else path.parent / target
    return destination / "index.html" if destination.is_dir() else destination


def test_every_page_has_one_top_level_heading():
    """Accessibility invariant: each page has exactly one h1."""
    for path, page in pages():
        assert page.h1_count == 1, path


def test_every_site_local_link_fragment_asset_and_image_resolves():
    for path, page in pages():
        for link in page.links:
            parsed = urlparse(link)
            if parsed.scheme or parsed.netloc:
                continue
            destination = resolve(path, link)
            assert destination.is_file(), (path, link)
            if parsed.fragment and destination.suffix == ".html":
                _, target = parsed_page(destination.relative_to(LANDING))
                assert parsed.fragment in target.ids, (path, link)
        for asset in page.assets:
            if not urlparse(asset).scheme:
                assert resolve(path, asset).is_file(), (path, asset)
        for image in page.images:
            assert image.get("alt") is not None, (path, image)
            src = str(image.get("src") or "")
            if urlparse(src).scheme:
                assert src.startswith(MEDIA_HOST), (path, src)
            else:
                assert resolve(path, src).is_file(), (path, src)
        for meta_img in page.meta_images:
            if urlparse(meta_img).scheme:
                assert meta_img.startswith((MEDIA_HOST, "https://openclinai.org/")), (path, meta_img)
            else:
                assert resolve(path, meta_img).is_file(), (path, meta_img)


def test_every_video_is_accessible_and_streamed_from_the_media_host():
    """Invariant: recordings live on the media host, never in this repository, and play accessibly."""
    for path, page in pages():
        for video in page.videos:
            assert "controls" in video and "playsinline" in video, path
            assert "autoplay" not in video, path
            assert video.get("preload") == "metadata", path
            assert video.get("aria-label"), path
            poster = str(video.get("poster") or "")
            assert poster.startswith(MEDIA_HOST) or local_asset(poster).is_file(), (path, poster)
        for source in page.sources:
            assert source.startswith(MEDIA_HOST), (path, source)


def test_pages_never_link_to_a_demo_host():
    """Forbidden coupling: public pages never depend on a demo server, which is stopped and redeployed."""
    for path, page in pages():
        urls = page.links + page.sources + page.assets + page.meta_images
        urls += [str(media.get(key) or "") for media in page.images + page.videos for key in ("src", "poster")]
        for url in urls:
            assert urlparse(url).hostname not in DEMO_HOSTS, (path, url)


def test_legacy_homepage_fragments_retain_onward_links():
    """Public URL stability: fragments that earlier versions of the homepage published keep resolving."""
    _, home = parsed_landing()
    assert {
        "project",
        "projects",
        "openmrs",
        "catalyst",
        "hub",
        "evidence",
        "wahs",
        "paths",
        "reporting-pathways",
        "reporting-path-1",
        "reporting-path-2",
        "reporting-path-3",
        "reporting-path-4",
        "catalyst-openelis-video",
        "catalyst-openmrs-video",
    } <= home.ids


def test_website_stack_is_static_and_independent_of_products():
    """Invariant: the website host serves read-only static content and never builds, proxies or mounts a product."""
    caddy = (ROOT / "compose" / "website" / "Caddyfile").read_text(encoding="utf-8")
    compose = yaml.safe_load((ROOT / "compose" / "website" / "services.yml").read_text(encoding="utf-8"))
    assert "reverse_proxy" not in caddy
    for name, service in compose["services"].items():
        assert "build" not in service and "depends_on" not in service, name
        for volume in service.get("volumes", []):
            assert not any(product in volume for product in ("targets/", "openmrs", "spa-custom")), (name, volume)
            if volume.startswith((".", "/")):
                assert volume.endswith(":ro"), (name, volume)
