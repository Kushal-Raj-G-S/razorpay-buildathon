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

    # "prepaid" | "cod". This field doesn't exist in AP2, ACP, UCP or
    # UPI Reserve Pay -- every one of them only governs prepaid money
    # (see research/06-protocols.md). But 50-70% of real Indian D2C
    # orders are Cash on Delivery, and RTO on COD orders already runs
    # 20-40% (research/03). An agent placing dozens of COD orders needs
    # ZERO payment authorization to do it -- there's no protocol on
    # earth that gates this today. That's a real, India-specific hole,
    # not a generic security concern, so it gets a real field here.
    payment_mode: str = "prepaid"

    @property
    def total(self) -> int:
        """Total cost of everything in the cart, in paise."""
        return sum(item.price * item.quantity for item in self.items)
