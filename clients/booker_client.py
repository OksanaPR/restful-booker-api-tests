import os

import requests

BASE_URL = os.getenv("BASE_URL", "https://restful-booker.herokuapp.com")


class BookerClient:
    def __init__(self, base_url: str = BASE_URL, timeout: int = 10):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = timeout

    # HTTP layer
    def get(self, endpoint: str, **kwargs):
        return self.session.get(
            f"{self.base_url}/{endpoint}", timeout=self.timeout, **kwargs
        )

    def post(self, endpoint: str, body: dict, **kwargs):
        return self.session.post(
            f"{self.base_url}/{endpoint}", json=body, timeout=self.timeout, **kwargs
        )

    def put(self, endpoint: str, body: dict, **kwargs):
        return self.session.put(
            f"{self.base_url}/{endpoint}", json=body, timeout=self.timeout, **kwargs
        )

    def patch(self, endpoint: str, body: dict, **kwargs):
        return self.session.patch(
            f"{self.base_url}/{endpoint}", json=body, timeout=self.timeout, **kwargs
        )

    def delete(self, endpoint: str, **kwargs):
        return self.session.delete(
            f"{self.base_url}/{endpoint}", timeout=self.timeout, **kwargs
        )

    def close(self):
        self.session.close()

    # --- API layer
    def create_token(self, username: str, password: str):
        return self.post("auth", {"username": username, "password": password})

    def create_booking(self, body: dict, **kwargs):
        return self.post("booking", body, **kwargs)

    def get_booking_by_id(self, booking_id, **kwargs):
        return self.get(f"booking/{booking_id}", **kwargs)

    def get_booking_ids(self, **filters):
        return self.get("booking", params=filters)

    def replace_booking(self, booking_id, body: dict, **kwargs):
        return self.put(f"booking/{booking_id}", body, **kwargs)

    def update_booking(self, booking_id, body: dict, **kwargs):
        return self.patch(f"booking/{booking_id}", body, **kwargs)

    def delete_booking(self, booking_id, **kwargs):
        return self.delete(f"booking/{booking_id}", **kwargs)

    def ping(self):
        return self.get("ping")
