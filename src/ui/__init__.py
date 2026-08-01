"""Presentation layer.

Turns already-fetched data into something a human can read. Per Architecture §3
and ADR-002, this layer is pure formatting: it never queries the database or the
API, which is what makes it easy to test now and easy to replace with a web view
later.
"""
