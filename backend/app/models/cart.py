"""
What a shopping cart looks like when an AI sends it to us.

Kept close to the UCP standard's field names (see research/06-protocols.md)
so this looks like a real industry cart, not something we invented.
"""
from pydantic import BaseModel
from typing import Optional


class CartItem(BaseModel):
    id: str                      # product id, e.g. "shirt-blue-L"
    title: str                   # "Blue Cotton Shirt, Large"
    price: int                   # in paise (450 rupees = 45000). Whole numbers only, no rounding bugs.
    currency: str = "INR"
    category: Optional[str] = None   # "clothing", "gift_card", etc — this is what deny_categories checks
    quantity: int = 1


class Cart(BaseModel):
    id: str
    items: list[CartItem]
    merchant_id: str

    @property
    def total(self) -> int:
        """Total cost of everything in the cart, in paise."""
        return sum(item.price * item.quantity for item in self.items)
