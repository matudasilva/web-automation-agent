from __future__ import annotations

from src.pages.base_page import BasePage


class LandingPage(BasePage):
    def assert_loaded(self, base_url: str, allowed_domain: str) -> None:
        self.assert_in_allowed_domain(allowed_domain=allowed_domain)
        self.assert_in_base_domain(base_url=base_url)
