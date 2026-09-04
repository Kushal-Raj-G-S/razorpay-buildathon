"""
What a shop's product list looks like once we've cleaned it up for an AI
to read. Field names match the UCP industry standard (research/06) so
this looks like a real catalog, not something we invented.
"""
from pydantic import BaseModel
from typing import Optional


class Variant(BaseModel):
    id: str                       # "shirt-blue-L" -- this becomes CartItem.id later
    title: str                    # "Blue, Large"
    price: int                    # paise
    currency: str = "INR"
    category: Optional[str] = None
    available: bool = True
    sku: Optional[str] = None


class Product(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    variants: list[Variant]


class Catalog(BaseModel):
    merchant_id: str
    products: list[Product]

    def find_variant(self, variant_id: str) -> Optional[Variant]:
        for product in self.products:
            for v in product.variants:
                if v.id == variant_id:
                    return v
        return None


class CatalogSaveResponse(BaseModel):
    status: str
    product_count: int


class CatalogFromTextResponse(BaseModel):
    status: str
    product_count: int
    catalog: Catalog


class CatalogSearchResponse(BaseModel):
    products: list[Product]
