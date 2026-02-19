"""Application port re-exporting the domain ProductRepository Protocol."""

from src.domain.repositories.product_repository import ProductRepository

ProductRepositoryPort = ProductRepository

__all__ = ["ProductRepositoryPort"]
